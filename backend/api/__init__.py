from flask import Blueprint

from api.auth import auth_bp
from api.diagnose import diagnose_bp
from api.diagnoses import diagnoses_bp
from api.health import health_bp
from api.images import images_bp
from api.patients import patients_bp
from api.stats import stats_bp
from api.users import users_bp


api_bp = Blueprint("api", __name__, url_prefix="/api")
api_bp.register_blueprint(auth_bp)
api_bp.register_blueprint(health_bp)
api_bp.register_blueprint(patients_bp)
api_bp.register_blueprint(diagnoses_bp)
api_bp.register_blueprint(diagnose_bp)
api_bp.register_blueprint(images_bp)
api_bp.register_blueprint(stats_bp)
api_bp.register_blueprint(users_bp)
