from __future__ import annotations

from pathlib import Path

from flask import Flask
from flask_cors import CORS
from sqlalchemy import inspect, text

from api import api_bp
from config import Config
from errors import register_error_handlers
from extensions import db, migrate


def create_app(config_object: type[Config] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object or Config)

    _ensure_runtime_dirs(app)
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    app.register_blueprint(api_bp)
    register_error_handlers(app)
    register_cli_commands(app)

    return app


def _ensure_runtime_dirs(app: Flask) -> None:
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["CONTOUR_FOLDER"]).mkdir(parents=True, exist_ok=True)


def _ensure_compatible_schema() -> None:
    inspector = inspect(db.engine)
    if "diagnoses" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("diagnoses")}
    if "lesion_positions" not in columns:
        db.session.execute(text("ALTER TABLE diagnoses ADD COLUMN lesion_positions TEXT NOT NULL DEFAULT '{}'"))
        db.session.commit()


def register_cli_commands(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db_command():
        db.create_all()
        _ensure_compatible_schema()
        print("Database tables created.")


if __name__ == "__main__":
    application = create_app()
    with application.app_context():
        db.create_all()
        _ensure_compatible_schema()
    application.run(host="0.0.0.0", port=5000, debug=application.config["DEBUG"])
