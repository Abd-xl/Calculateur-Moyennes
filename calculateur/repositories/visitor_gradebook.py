"""Adaptateur SQLAlchemy entre un profil visiteur et l'état métier."""

from copy import deepcopy

from calculateur.models import Grade, Subject
from calculateur.services.validation import validate_data


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


def save_gradebook(visitor, data, session):
    validate_data(data)
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

    # Keep the previous shape synchronized until the rollback window closes.
    visitor.data = deepcopy(data)
    visitor.data_initialized = True
    session.commit()
