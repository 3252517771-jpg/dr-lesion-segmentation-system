from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Index, Text
from sqlalchemy.types import TypeDecorator

from extensions import db


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class JSONField(TypeDecorator):
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return "{}"
        return json.dumps(value, ensure_ascii=False)

    def process_result_value(self, value, dialect):
        if not value:
            return {}
        return json.loads(value)


class Patient(db.Model):
    __tablename__ = "patients"
    __table_args__ = (
        CheckConstraint("age >= 0 AND age <= 150", name="ck_patients_age_range"),
        Index("idx_patients_patient_id", "patient_id"),
        Index("idx_patients_name", "name"),
        Index("idx_patients_deleted", "is_deleted"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    patient_id = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    diagnoses = db.relationship("Diagnosis", back_populates="patient", lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "gender": self.gender,
            "age": self.age,
            "patient_id": self.patient_id,
            "diagnosis_count": self.diagnoses.filter_by(is_deleted=False).count(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def soft_delete(self) -> None:
        self.is_deleted = True
        for diagnosis in self.diagnoses.filter_by(is_deleted=False).all():
            diagnosis.soft_delete()


class Diagnosis(db.Model):
    __tablename__ = "diagnoses"
    __table_args__ = (
        Index("idx_diagnoses_patient", "patient_id"),
        Index("idx_diagnoses_created", "created_at"),
        Index("idx_diagnoses_deleted", "is_deleted"),
        Index("idx_diagnoses_patient_active", "patient_id", "is_deleted"),
    )

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)
    contour_path = db.Column(db.String(500), nullable=True)
    lesion_areas = db.Column(JSONField, default=dict, nullable=False)
    lesion_counts = db.Column(JSONField, default=dict, nullable=False)
    severity = db.Column(db.String(50), default="正常", nullable=False)
    notes = db.Column(db.Text, default="", nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    patient = db.relationship("Patient", back_populates="diagnoses")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "patient_name": self.patient.name if self.patient else None,
            "image_path": self.image_path,
            "contour_path": self.contour_path,
            "lesion_areas": self.lesion_areas,
            "lesion_counts": self.lesion_counts,
            "severity": self.severity,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def soft_delete(self) -> None:
        self.is_deleted = True
