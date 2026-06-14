from __future__ import annotations

from flask import Blueprint, jsonify, request

from errors import AuthenticationError, ValidationError
from services.auth_service import AuthService, login_required


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    if not username or not password:
        raise ValidationError("用户名和密码不能为空")

    user = AuthService.login(username, password)
    return jsonify({"user": user.to_dict()})


@auth_bp.post("/logout")
@login_required
def logout():
    AuthService.logout()
    return jsonify({"success": True})


@auth_bp.get("/me")
def me():
    user = AuthService.current_user()
    if not user:
        raise AuthenticationError()
    return jsonify({"user": user.to_dict()})
