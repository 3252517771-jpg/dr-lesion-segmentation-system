from __future__ import annotations

from database.models import Diagnosis
from errors import DiagnosisNotFoundError, ValidationError
from extensions import db
from services.patient_service import PatientService


class DiagnosisService:
    @staticmethod
    def list_diagnoses(page: int = 1, size: int = 10, patient_id: int | None = None) -> dict:
        page = max(page, 1)
        size = min(max(size, 1), 100)

        query = Diagnosis.query.filter_by(is_deleted=False)
        if patient_id is not None:
            query = query.filter_by(patient_id=patient_id)

        pagination = query.order_by(Diagnosis.created_at.desc()).paginate(page=page, per_page=size, error_out=False)
        return {
            "diagnoses": [diagnosis.to_dict() for diagnosis in pagination.items],
            "total": pagination.total,
            "page": page,
            "size": size,
        }

    @staticmethod
    def create_diagnosis(
        patient_id: int,
        image_path: str,
        contour_path: str | None,
        lesion_areas: dict,
        lesion_counts: dict,
        severity: str,
        notes: str = "",
    ) -> Diagnosis:
        PatientService.get_patient(patient_id)
        if not image_path:
            raise ValidationError("原图路径不能为空")

        diagnosis = Diagnosis(
            patient_id=patient_id,
            image_path=image_path,
            contour_path=contour_path,
            lesion_areas=lesion_areas or {},
            lesion_counts=lesion_counts or {},
            severity=severity or "正常",
            notes=notes or "",
        )
        db.session.add(diagnosis)
        db.session.commit()
        return diagnosis

    @staticmethod
    def get_diagnosis(diagnosis_id: int) -> Diagnosis:
        diagnosis = Diagnosis.query.filter_by(id=diagnosis_id, is_deleted=False).first()
        if not diagnosis:
            raise DiagnosisNotFoundError()
        return diagnosis

    @staticmethod
    def update_notes(diagnosis_id: int, notes: str) -> Diagnosis:
        diagnosis = DiagnosisService.get_diagnosis(diagnosis_id)
        diagnosis.notes = notes or ""
        db.session.commit()
        return diagnosis

    @staticmethod
    def delete_diagnosis(diagnosis_id: int) -> None:
        diagnosis = DiagnosisService.get_diagnosis(diagnosis_id)
        diagnosis.soft_delete()
        db.session.commit()
