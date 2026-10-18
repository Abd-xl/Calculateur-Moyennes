"""Audit en lecture seule des copies JSON et relationnelles des gradebooks."""

import json
import math

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from calculateur.models import Subject, Visitor
from calculateur.services.grades import calculate_averages
from calculateur.services.validation import validate_data


def _legacy_gradebook(value):
    if isinstance(value, str):
        value = json.loads(value)
    validate_data(value)
    return value


def _relational_gradebook(visitor):
    notes = {}
    coefficients = {}
    issues = []

    for subject_position, subject in enumerate(visitor.subjects):
        if subject.position != subject_position:
            issues.append(f"position de matière inattendue: {subject.name}")
        coefficients[subject.name] = subject.coefficient
        notes[subject.name] = []
        for grade_position, grade in enumerate(subject.grades):
            if grade.position != grade_position:
                issues.append(
                    f"position de note inattendue: {subject.name}[{grade_position}]"
                )
            notes[subject.name].append({"note": grade.value, "bareme": grade.scale})

    return {"notes": notes, "coef": coefficients}, issues


def audit_gradebooks(session, batch_size=500, max_issues=50):
    """Compare les deux formats par lots sans écrire dans la base."""
    report = {
        "profiles": 0,
        "initialized_profiles": 0,
        "legacy_subjects": 0,
        "relational_subjects": 0,
        "legacy_grades": 0,
        "relational_grades": 0,
        "profiles_with_issues": 0,
        "issues": [],
        "issue_count": 0,
    }
    last_id = 0

    while True:
        visitors = session.scalars(
            select(Visitor)
            .where(Visitor.id > last_id)
            .order_by(Visitor.id)
            .limit(batch_size)
            .options(selectinload(Visitor.subjects).selectinload(Subject.grades))
        ).all()
        if not visitors:
            break

        for visitor in visitors:
            last_id = visitor.id
            report["profiles"] += 1
            report["initialized_profiles"] += int(visitor.data_initialized)
            profile_issues = []
            relational, relational_issues = _relational_gradebook(visitor)
            profile_issues.extend(relational_issues)

            report["relational_subjects"] += len(relational["notes"])
            report["relational_grades"] += sum(
                len(grades) for grades in relational["notes"].values()
            )

            try:
                legacy = _legacy_gradebook(visitor.data)
                report["legacy_subjects"] += len(legacy["notes"])
                report["legacy_grades"] += sum(
                    len(grades) for grades in legacy["notes"].values()
                )
                if list(legacy["notes"]) != list(relational["notes"]):
                    profile_issues.append("ordre ou liste des matières différent")
                if legacy != relational:
                    profile_issues.append("contenu JSON et relationnel différent")

                validate_data(relational)
                legacy_averages, legacy_overall = calculate_averages(legacy)
                relational_averages, relational_overall = calculate_averages(relational)
                same_averages = (
                    legacy_averages.keys() == relational_averages.keys()
                    and all(
                        math.isclose(
                            legacy_averages[name], relational_averages[name],
                            rel_tol=1e-12, abs_tol=1e-12,
                        )
                        for name in legacy_averages
                    )
                    and math.isclose(
                        legacy_overall, relational_overall,
                        rel_tol=1e-12, abs_tol=1e-12,
                    )
                )
                if not same_averages:
                    profile_issues.append("moyennes différentes")
            except (TypeError, ValueError, json.JSONDecodeError) as error:
                profile_issues.append(f"données invalides: {error}")

            if profile_issues:
                report["profiles_with_issues"] += 1
                report["issue_count"] += len(profile_issues)
                if len(report["issues"]) < max_issues:
                    report["issues"].append({"visitor_id": visitor.id, "details": profile_issues})

    return report
