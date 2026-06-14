from __future__ import annotations

from flask import jsonify


class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


class ValidationError(AppError):
    def __init__(self, message: str):
        super().__init__("VALIDATION_ERROR", message, 400)


class PatientNotFoundError(AppError):
    def __init__(self):
        super().__init__("PATIENT_NOT_FOUND", "患者不存在", 404)


class DiagnosisNotFoundError(AppError):
    def __init__(self):
        super().__init__("DIAGNOSIS_NOT_FOUND", "诊断记录不存在", 404)


class DuplicatePatientIdError(AppError):
    def __init__(self):
        super().__init__("DUPLICATE_PATIENT_ID", "病历号已存在", 400)


class UserNotFoundError(AppError):
    def __init__(self):
        super().__init__("USER_NOT_FOUND", "用户不存在", 404)


class DuplicateUsernameError(AppError):
    def __init__(self):
        super().__init__("DUPLICATE_USERNAME", "用户名已存在", 400)


class AuthenticationError(AppError):
    def __init__(self, message: str = "请先登录"):
        super().__init__("AUTHENTICATION_REQUIRED", message, 401)


class PermissionDeniedError(AppError):
    def __init__(self, message: str = "没有权限执行该操作"):
        super().__init__("PERMISSION_DENIED", message, 403)


class InvalidImageError(AppError):
    def __init__(self, message: str = "图片格式不支持"):
        super().__init__("INVALID_IMAGE", message, 400)


class ModelLoadError(AppError):
    def __init__(self):
        super().__init__("MODEL_LOAD_FAILED", "模型加载失败", 500)


class InferenceError(AppError):
    def __init__(self, message: str = "推理失败"):
        super().__init__("INFERENCE_FAILED", message, 500)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error: AppError):
        return jsonify({"error": {"code": error.code, "message": error.message}}), error.status

    @app.errorhandler(404)
    def handle_not_found(_error):
        return jsonify({"error": {"code": "NOT_FOUND", "message": "资源不存在"}}), 404

    @app.errorhandler(413)
    def handle_too_large(_error):
        return jsonify({"error": {"code": "FILE_TOO_LARGE", "message": "图片大小不能超过 10MB"}}), 413

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        if app.config.get("TESTING"):
            raise error
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": "服务器内部错误"}}), 500
