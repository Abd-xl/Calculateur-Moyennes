"""Précontrôle en lecture seule des profils JSON avant la migration relationnelle."""

import json

from sqlalchemy import MetaData, Table, Text, cast, inspect, select

from calculateur.services.grades import calculate_averages
from calculateur.services.validation import validate_data


def _decode_gradebook(raw):
    value = json.loads(raw) if isinstance(raw, str) else raw
    validate_data(value)
    return value


def preflight_gradebooks(connection, batch_size=500, max_issues=50):
    """Valide les données legacy et établit les comptes sans modifier la base."""
    report = {
        "source_table_found": False,
        "profiles": 0,
        "valid_profiles": 0,
        "subjects": 0,
        "grades": 0,
        "subject_average_sum": 0.0,
        "overall_average_sum": 0.0,
        "profiles_with_issues": 0,
        "issues": [],
    }
    inspector = inspect(connection)
    if "anonymous_visitors" not in inspector.get_table_names():
        return report

    report["source_table_found"] = True
    columns = {column["name"] for column in inspector.get_columns("anonymous_visitors")}
    missing = {"id", "data"} - columns
    if missing:
        report["profiles_with_issues"] = 1
        report["issues"].append(
            {"visitor_id": None, "details": [f"colonnes manquantes: {', '.join(sorted(missing))}"]}
        )
        return report

    visitors = Table("anonymous_visitors", MetaData(), autoload_with=connection)
    last_id = 0
    while True:
        rows = connection.execute(
            select(visitors.c.id, cast(visitors.c.data, Text).label("data_text"))
            .where(visitors.c.id > last_id)
            .order_by(visitors.c.id)
            .limit(batch_size)
        ).mappings().all()
        if not rows:
            break

        for row in rows:
            last_id = row["id"]
            report["profiles"] += 1
            try:
                data = _decode_gradebook(row["data_text"])
                averages, overall = calculate_averages(data)
                report["valid_profiles"] += 1
                report["subjects"] += len(data["notes"])
                report["grades"] += sum(len(grades) for grades in data["notes"].values())
                report["subject_average_sum"] += sum(averages.values())
                report["overall_average_sum"] += overall
            except (TypeError, ValueError, json.JSONDecodeError) as error:
                report["profiles_with_issues"] += 1
                if len(report["issues"]) < max_issues:
                    report["issues"].append(
                        {"visitor_id": row["id"], "details": [f"JSON invalide: {error}"]}
                    )

    return report
