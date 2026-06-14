from __future__ import annotations

from flask import Blueprint, jsonify, request

from services.auth_service import doctor_required
from services.user_service import UserService


users_bp = Blueprint("users", __name__, url_prefix="/users")


@users_bp.get("")
@doctor_required
def list_users():
    result = UserService.list_users(
        page=request.args.get("page", 1, type=int),
        size=request.args.get("size", 10, type=int),
        search=request.args.get("search", type=str),
        role=request.args.get("role", type=str),
    )
    return jsonify(result)


@users_bp.post("")
@doctor_required
def create_user():
    user = UserService.create_user(request.get_json(silent=True) or {})
    return jsonify({"user": user.to_dict()}), 201


@users_bp.get("/<int:user_id>")
@doctor_required
def get_user(user_id: int):
    user = UserService.get_user(user_id)
    return jsonify({"user": user.to_dict()})


@users_bp.put("/<int:user_id>")
@doctor_required
def update_user(user_id: int):
    user = UserService.update_user(user_id, request.get_json(silent=True) or {})
    return jsonify({"user": user.to_dict()})


@users_bp.delete("/<int:user_id>")
@doctor_required
def delete_user(user_id: int):
    UserService.delete_user(user_id)
    return jsonify({"success": True})
