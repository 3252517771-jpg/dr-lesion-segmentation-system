from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from database.models import Patient
from errors import DuplicatePatientIdError, PatientNotFoundError, ValidationError
from extensions import db


class PatientService:
    @staticmethod
    def list_patients(page: int = 1, size: int = 10, search: str | None = None) -> dict:
        page = max(page, 1)
        size = min(max(size, 1), 100)

        query = Patient.query.filter_by(is_deleted=False)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter((Patient.name.like(pattern)) | (Patient.patient_id.like(pattern)))

        pagination = query.order_by(Patient.created_at.desc()).paginate(page=page, per_page=size, error_out=False)
        return {
            "patients": [patient.to_dict() for patient in pagination.items],
            "total": pagination.total,
            "page": page,
            "size": size,
        }

    @staticmethod
    def create_patient(data: dict) -> Patient:
        PatientService._validate_required(data, ("name", "gender", "age", "patient_id"))
        age = PatientService._validate_age(data.get("age"))

        patient = Patient(
            name=str(data["name"]).strip(),
            gender=str(data["gender"]).strip(),
            age=age,
            patient_id=str(data["patient_id"]).strip(),
        )
        db.session.add(patient)
        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise DuplicatePatientIdError() from exc
        return patient

    @staticmethod
    def get_patient(patient_pk: int) -> Patient:
        patient = Patient.query.filter_by(id=patient_pk, is_deleted=False).first()
        if not patient:
            raise PatientNotFoundError()
        return patient

    @staticmethod
    def update_patient(patient_pk: int, data: dict) -> Patient:
        patient = PatientService.get_patient(patient_pk)

        if "name" in data:
            name = str(data["name"]).strip()
            if not name:
                raise ValidationError("患者姓名不能为空")
            patient.name = name
        if "gender" in data:
            gender = str(data["gender"]).strip()
            if not gender:
                raise ValidationError("患者性别不能为空")
            patient.gender = gender
        if "age" in data:
            patient.age = PatientService._validate_age(data["age"])
        if "patient_id" in data:
            patient_id = str(data["patient_id"]).strip()
            if not patient_id:
                raise ValidationError("病历号不能为空")
            patient.patient_id = patient_id

        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise DuplicatePatientIdError() from exc
        return patient

    @staticmethod
    def delete_patient(patient_pk: int) -> None:
        patient = PatientService.get_patient(patient_pk)
        patient.soft_delete()
        db.session.commit()

    @staticmethod
    def _validate_required(data: dict, fields: tuple[str, ...]) -> None:
        for field in fields:
            if field not in data or str(data[field]).strip() == "":
                raise ValidationError(f"{field} 不能为空")

    @staticmethod
    def _validate_age(value) -> int:
        try:
            age = int(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError("年龄必须是整数") from exc
        if age < 0 or age > 150:
            raise ValidationError("年龄必须在 0 到 150 之间")
        return age
