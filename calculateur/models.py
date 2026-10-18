"""Modèles de persistance SQLAlchemy."""

from datetime import datetime, timezone

from calculateur.extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class Visitor(db.Model):
    __tablename__ = "anonymous_visitors"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    token_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    browser_info = db.Column(db.String(512), nullable=False, default="Inconnu")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    last_seen_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    data = db.Column(db.JSON, nullable=False, default=lambda: {"notes": {}, "coef": {}})
    # False until the browser has completed its first successful synchronization.
    data_initialized = db.Column(db.Boolean, nullable=False, default=False)
    # Incremented with compare-and-swap whenever the gradebook changes.
    gradebook_version = db.Column(db.Integer, nullable=False, default=1, server_default="1")
    subjects = db.relationship(
        "Subject",
        back_populates="visitor",
        cascade="all, delete-orphan",
        order_by="Subject.position",
    )


class Subject(db.Model):
    __tablename__ = "subjects"
    __table_args__ = (
        db.UniqueConstraint("visitor_id", "name", name="uq_subject_visitor_name"),
        db.CheckConstraint("coefficient > 0", name="ck_subject_coefficient_positive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    visitor_id = db.Column(
        db.Integer,
        db.ForeignKey("anonymous_visitors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.Text, nullable=False)
    coefficient = db.Column(db.Integer, nullable=False)
    position = db.Column(db.Integer, nullable=False)
    visitor = db.relationship("Visitor", back_populates="subjects")
    grades = db.relationship(
        "Grade",
        back_populates="subject",
        cascade="all, delete-orphan",
        order_by="Grade.position",
    )


class Grade(db.Model):
    __tablename__ = "grades"
    __table_args__ = (
        db.CheckConstraint("scale IN (10, 20)", name="ck_grade_scale_valid"),
        db.CheckConstraint("value >= 0", name="ck_grade_value_nonnegative"),
        db.CheckConstraint("value <= scale", name="ck_grade_value_within_scale"),
        db.UniqueConstraint("subject_id", "position", name="uq_grade_subject_position"),
    )

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    value = db.Column(db.Float, nullable=False)
    scale = db.Column(db.Integer, nullable=False)
    position = db.Column(db.Integer, nullable=False)
    subject = db.relationship("Subject", back_populates="grades")
