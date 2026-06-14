from __future__ import annotations

from flask import Blueprint, jsonify, request

from services.auth_service import AuthService, doctor_required, login_required
from services.patient_service import PatientService


patients_bp = Blueprint("patients", __name__, url_prefix="/patients")


@patients_bp.get("")
@login_required
def list_patients():
    user = AuthService.require_user()
    if user.role == "patient":
        patient = PatientService.get_patient(user.linked_patient_id)
        return jsonify({"patients": [patient.to_dict()], "total": 1, "page": 1, "size": 1})

    result = PatientService.list_patients(
        page=request.args.get("page", 1, type=int),
        size=request.args.get("size", 10, type=int),
        search=request.args.get("search", type=str),
    )
    return jsonify(result)


@patients_bp.post("")
@doctor_required
def create_patient():
    patient = PatientService.create_patient(request.get_json(silent=True) or {})
    return jsonify({"patient": patient.to_dict()}), 201


@patients_bp.get("/<int:patient_id>")
@login_required
def get_patient(patient_id: int):
    AuthService.ensure_patient_access(patient_id)
    patient = PatientService.get_patient(patient_id)
    return jsonify({"patient": patient.to_dict()})


@patients_bp.put("/<int:patient_id>")
@doctor_required
def update_patient(patient_id: int):
    patient = PatientService.update_patient(patient_id, request.get_json(silent=True) or {})
    return jsonify({"patient": patient.to_dict()})


@patients_bp.delete("/<int:patient_id>")
@doctor_required
def delete_patient(patient_id: int):
    PatientService.delete_patient(patient_id)
    return jsonify({"success": True})
