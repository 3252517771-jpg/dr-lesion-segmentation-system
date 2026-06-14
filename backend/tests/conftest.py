from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import create_app, init_runtime_database
from config import TestConfig
from extensions import db


@pytest.fixture()
def app():
    flask_app = create_app(TestConfig)
    with flask_app.app_context():
        init_runtime_database(flask_app)
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    test_client = app.test_client()
    test_client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    return test_client


@pytest.fixture()
def anonymous_client(app):
    return app.test_client()
