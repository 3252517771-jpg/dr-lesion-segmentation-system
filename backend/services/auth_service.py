from __future__ import annotations

from functools import wraps
from typing import Callable, TypeVar

from flask import session
from werkzeug.security import check_password_hash

from database.models import Diagnosis, User
from errors import AuthenticationError, PermissionDeniedError

F = TypeVar("F", bound=Callable)


class AuthService:
    @staticmethod
    def login(username: str, password: str) -> User:
        user = User.query.filter_by(username=username.strip(), is_deleted=False).first()
        if not user or not user.is_active or not check_password_hash(user.password_hash, password):
            raise AuthenticationError("用户名或密码错误")
        session["user_id"] = user.id
        return user

    @staticmethod
    def logout() -> None:
        session.pop("user_id", None)

    @staticmethod
    def current_user() -> User | None:
        user_id = session.get("user_id")
        if not user_id:
            return None
        return User.query.filter_by(id=user_id, is_deleted=False, is_active=True).first()

    @staticmethod
    def require_user() -> User:
        user = AuthService.current_user()
        if not user:
            raise AuthenticationError()
        return user

    @staticmethod
    def require_doctor() -> User:
        user = AuthService.require_user()
        if user.role != "doctor":
            raise PermissionDeniedError()
        return user

    @staticmethod
    def can_access_patient(user: User, patient_id: int) -> bool:
        return user.role == "doctor" or user.linked_patient_id == patient_id

    @staticmethod
    def ensure_patient_access(patient_id: int) -> User:
        user = AuthService.require_user()
        if not AuthService.can_access_patient(user, patient_id):
            raise PermissionDeniedError("只能访问自己的患者资料")
        return user

    @staticmethod
    def ensure_diagnosis_access(diagnosis: Diagnosis) -> User:
        user = AuthService.require_user()
        if not AuthService.can_access_patient(user, diagnosis.patient_id):
            raise PermissionDeniedError("只能访问自己的诊断记录")
        return user


def login_required(fn: F) -> F:
    @wraps(fn)
    def wrapper(*args, **kwargs):
        AuthService.require_user()
        return fn(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


def doctor_required(fn: F) -> F:
    @wraps(fn)
    def wrapper(*args, **kwargs):
        AuthService.require_doctor()
        return fn(*args, **kwargs)

    return wrapper  # type: ignore[return-value]
