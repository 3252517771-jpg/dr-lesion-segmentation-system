from __future__ import annotations

from flask import Blueprint, jsonify, request

from errors import ValidationError
from services.diagnosis_service import DiagnosisService


diagnoses_bp = Blueprint("diagnoses", __name__, url_prefix="/diagnoses")


@diagnoses_bp.get("")
def list_diagnoses():
    result = DiagnosisService.list_diagnoses(
        page=request.args.get("page", 1, type=int),
        size=request.args.get("size", 10, type=int),
        patient_id=request.args.get("patient_id", type=int),
    )
    return jsonify(result)


@diagnoses_bp.post("")
def create_diagnosis():
    data = request.get_json(silent=True) or {}
    if "patient_id" not in data:
        raise ValidationError("患者 ID 不能为空")
    try:
        patient_id = int(data["patient_id"])
    except (TypeError, ValueError) as exc:
        raise ValidationError("患者 ID 必须是整数") from exc

    diagnosis = DiagnosisService.create_diagnosis(
        patient_id=patient_id,
        image_path=data.get("image_path", ""),
        contour_path=data.get("contour_path"),
        lesion_areas=data.get("lesion_areas", {}),
        lesion_counts=data.get("lesion_counts", {}),
        lesion_positions=data.get("lesion_positions", {}),
        severity=data.get("severity", "正常"),
        notes=data.get("notes", ""),
    )
    return jsonify({"diagnosis": diagnosis.to_dict()}), 201


@diagnoses_bp.get("/<int:diagnosis_id>")
def get_diagnosis(diagnosis_id: int):
    diagnosis = DiagnosisService.get_diagnosis(diagnosis_id)
    return jsonify({"diagnosis": diagnosis.to_dict()})


@diagnoses_bp.put("/<int:diagnosis_id>")
def update_diagnosis_notes(diagnosis_id: int):
    data = request.get_json(silent=True) or {}
    diagnosis = DiagnosisService.update_notes(diagnosis_id, data.get("notes", ""))
    return jsonify({"diagnosis": diagnosis.to_dict()})


@diagnoses_bp.delete("/<int:diagnosis_id>")
def delete_diagnosis(diagnosis_id: int):
    DiagnosisService.delete_diagnosis(diagnosis_id)
    return jsonify({"success": True})
