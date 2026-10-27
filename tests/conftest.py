"""Shared fixtures that isolate tests from the configured application database."""

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.models import Asset, Category, Department, User, db


@pytest.fixture
def app(tmp_path):
    """Create a fresh temporary database and a known test user."""
    test_app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-only-secret",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}",
            "SEED_DEMO_DATA": False,
            "LLM_API_KEY": "",
            "INITIAL_ADMIN_USERNAME": "",
            "INITIAL_ADMIN_EMAIL": "",
            "INITIAL_ADMIN_PASSWORD": "",
            "INITIAL_ADMIN_FULL_NAME": "",
        }
    )
    with test_app.app_context():
        db.session.add_all(
            [
                User(
                    username="test-admin",
                    email="test-admin@example.invalid",
                    password_hash=generate_password_hash("test-password-123"),
                    role="admin",
                    full_name="Test Admin",
                ),
                User(
                    username="test-manager",
                    email="test-manager@example.invalid",
                    password_hash=generate_password_hash("test-password-123"),
                    role="manager",
                    full_name="Test Manager",
                ),
                User(
                    username="test-inspector",
                    email="test-inspector@example.invalid",
                    password_hash=generate_password_hash("test-password-123"),
                    role="inspector",
                    full_name="Test Inspector",
                ),
                User(
                    username="test-staff",
                    email="test-staff@example.invalid",
                    password_hash=generate_password_hash("test-password-123"),
                    role="staff",
                    full_name="Test Staff",
                ),
                Category(name="Thiết bị"),
                Department(name="Phòng A", code="A"),
                Department(name="Phòng B", code="B"),
            ]
        )
        db.session.flush()
        db.session.add(
            Asset(
                asset_code="TEST-001",
                name="Máy tính thử nghiệm",
                category_id=Category.query.one().id,
                department_id=Department.query.filter_by(code="A").one().id,
                value=1000,
                status="active",
            )
        )
        db.session.commit()
    yield test_app
    with test_app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def authenticated_client(client):
    client.post(
        "/login",
        data={"username": "test-admin", "password": "test-password-123"},
    )
    return client
