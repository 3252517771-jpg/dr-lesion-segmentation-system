from flask import Blueprint

from api.diagnoses import diagnoses_bp
from api.health import health_bp
from api.patients import patients_bp


api_bp = Blueprint("api", __name__, url_prefix="/api")
api_bp.register_blueprint(health_bp)
api_bp.register_blueprint(patients_bp)
api_bp.register_blueprint(diagnoses_bp)
