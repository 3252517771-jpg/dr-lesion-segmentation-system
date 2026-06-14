from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from database.models import User
from errors import DuplicateUsernameError, UserNotFoundError, ValidationError
from extensions import db
from services.patient_service import PatientService

VALID_ROLES = {"doctor", "patient"}


class UserService:
    @staticmethod
    def list_users(page: int = 1, size: int = 10, search: str | None = None, role: str | None = None) -> dict:
        page = max(page, 1)
        size = min(max(size, 1), 100)

        query = User.query.filter_by(is_deleted=False)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter((User.username.like(pattern)) | (User.display_name.like(pattern)))
        if role:
            if role not in VALID_ROLES:
                raise ValidationError("角色只能是 doctor 或 patient")
            query = query.filter_by(role=role)

        pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=size, error_out=False)
        return {
            "users": [user.to_dict() for user in pagination.items],
            "total": pagination.total,
            "page": page,
            "size": size,
        }

    @staticmethod
    def create_user(data: dict) -> User:
        UserService._validate_required(data, ("username", "display_name", "password", "role"))
        role = UserService._validate_role(data.get("role"))
        linked_patient_id = UserService._validate_linked_patient(role, data.get("linked_patient_id"))

        user = User(
            username=str(data["username"]).strip(),
            display_name=str(data["display_name"]).strip(),
            password_hash=generate_password_hash(str(data["password"])),
            role=role,
            linked_patient_id=linked_patient_id,
            is_active=bool(data.get("is_active", True)),
        )
        db.session.add(user)
        UserService._commit_or_duplicate()
        return user

    @staticmethod
    def get_user(user_id: int) -> User:
        user = User.query.filter_by(id=user_id, is_deleted=False).first()
        if not user:
            raise UserNotFoundError()
        return user

    @staticmethod
    def update_user(user_id: int, data: dict) -> User:
        user = UserService.get_user(user_id)
        role = user.role

        if "username" in data:
            username = str(data["username"]).strip()
            if not username:
                raise ValidationError("用户名不能为空")
            user.username = username
        if "display_name" in data:
            display_name = str(data["display_name"]).strip()
            if not display_name:
                raise ValidationError("显示名称不能为空")
            user.display_name = display_name
        if "role" in data:
            role = UserService._validate_role(data.get("role"))
            user.role = role
        if "linked_patient_id" in data or "role" in data:
            user.linked_patient_id = UserService._validate_linked_patient(role, data.get("linked_patient_id"))
        if "is_active" in data:
            user.is_active = bool(data["is_active"])
        if data.get("password"):
            user.password_hash = generate_password_hash(str(data["password"]))

        UserService._commit_or_duplicate()
        return user

    @staticmethod
    def delete_user(user_id: int) -> None:
        user = UserService.get_user(user_id)
        user.soft_delete()
        db.session.commit()

    @staticmethod
    def ensure_default_admin(username: str, password: str, display_name: str) -> None:
        existing = User.query.filter_by(username=username, is_deleted=False).first()
        if existing:
            return
        admin = User(
            username=username,
            display_name=display_name,
            password_hash=generate_password_hash(password),
            role="doctor",
            is_active=True,
        )
        db.session.add(admin)
        db.session.commit()

    @staticmethod
    def _validate_required(data: dict, fields: tuple[str, ...]) -> None:
        for field in fields:
            if field not in data or str(data[field]).strip() == "":
                raise ValidationError(f"{field} 不能为空")

    @staticmethod
    def _validate_role(value) -> str:
        role = str(value).strip()
        if role not in VALID_ROLES:
            raise ValidationError("角色只能是 doctor 或 patient")
        return role

    @staticmethod
    def _validate_linked_patient(role: str, value) -> int | None:
        if role == "doctor":
            return None
        if value in (None, ""):
            raise ValidationError("病人账号必须关联患者")
        try:
            linked_patient_id = int(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError("关联患者 ID 必须是整数") from exc
        PatientService.get_patient(linked_patient_id)
        return linked_patient_id

    @staticmethod
    def _commit_or_duplicate() -> None:
        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise DuplicateUsernameError() from exc
