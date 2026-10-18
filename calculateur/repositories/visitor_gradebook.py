"""Adaptateur SQLAlchemy entre un profil visiteur et l'état métier."""

from copy import deepcopy

from sqlalchemy import update
from sqlalchemy.orm.attributes import set_committed_value

from calculateur.models import Grade, Subject, Visitor
from calculateur.services.validation import validate_data


class GradebookConflictError(Exception):
    """Raised when the caller edits a gradebook version that is no longer current."""


def load_gradebook(visitor):
    if not visitor.subjects and visitor.data:
        # Read compatibility data if a profile has not yet been backfilled.
        return deepcopy(visitor.data)

    notes = {}
    coefficients = {}
    for subject in visitor.subjects:
        coefficients[subject.name] = subject.coefficient
        notes[subject.name] = [
            {"note": grade.value, "bareme": grade.scale}
            for grade in subject.grades
        ]
    return {"notes": notes, "coef": coefficients}


def save_gradebook(visitor, data, session, expected_version):
    validate_data(data)

    next_version = expected_version + 1
    result = session.execute(
        update(Visitor)
        .where(
            Visitor.id == visitor.id,
            Visitor.gradebook_version == expected_version,
        )
        .values(
            data=deepcopy(data),
            data_initialized=True,
            gradebook_version=next_version,
        )
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        raise GradebookConflictError

    visitor.subjects.clear()
    session.flush()
    for subject_position, (name, grades) in enumerate(data["notes"].items()):
        subject = Subject(
            name=name,
            coefficient=data["coef"][name],
            position=subject_position,
        )
        subject.grades.extend(
            Grade(value=grade["note"], scale=grade["bareme"], position=position)
            for position, grade in enumerate(grades)
        )
        visitor.subjects.append(subject)

    # The conditional UPDATE already wrote these fields atomically.
    set_committed_value(visitor, "data", deepcopy(data))
    set_committed_value(visitor, "data_initialized", True)
    set_committed_value(visitor, "gradebook_version", next_version)
    session.commit()
    return next_version
