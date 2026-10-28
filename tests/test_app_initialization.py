"""Tests for safe, non-destructive application initialization."""

import pytest
from werkzeug.security import check_password_hash

from app import create_app
from app.models import User, db


def test_startup_does_not_create_default_users_or_demo_data(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-only-secret",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'empty.db'}",
            "SEED_DEMO_DATA": False,
            "INITIAL_ADMIN_USERNAME": "",
            "INITIAL_ADMIN_EMAIL": "",
            "INITIAL_ADMIN_PASSWORD": "",
            "INITIAL_ADMIN_FULL_NAME": "",
        }
    )

    with app.app_context():
        assert User.query.count() == 0


def test_initial_admin_is_created_once_and_password_is_not_reset(tmp_path):
    database_uri = f"sqlite:///{tmp_path / 'admin.db'}"
    config = {
        "TESTING": True,
        "SECRET_KEY": "test-only-secret",
        "SQLALCHEMY_DATABASE_URI": database_uri,
        "SEED_DEMO_DATA": False,
        "INITIAL_ADMIN_USERNAME": "first-admin",
        "INITIAL_ADMIN_EMAIL": "first-admin@example.invalid",
        "INITIAL_ADMIN_PASSWORD": "initial-secure-password",
        "INITIAL_ADMIN_FULL_NAME": "Initial Admin",
    }
    create_app(config)
    config["INITIAL_ADMIN_PASSWORD"] = "different-secure-password"
    app = create_app(config)

    with app.app_context():
        user = User.query.filter_by(username="first-admin").one()
        assert check_password_hash(user.password_hash, "initial-secure-password")
        assert not check_password_hash(user.password_hash, "different-secure-password")


def test_initial_staff_and_inspector_are_created_with_their_roles(tmp_path):
    database_uri = f"sqlite:///{tmp_path / 'non-manager-users.db'}"
    config = {
        "TESTING": True,
        "SECRET_KEY": "test-only-secret",
        "SQLALCHEMY_DATABASE_URI": database_uri,
        "SEED_DEMO_DATA": False,
        "INITIAL_INSPECTOR_USERNAME": "first-inspector",
        "INITIAL_INSPECTOR_EMAIL": "first-inspector@example.invalid",
        "INITIAL_INSPECTOR_PASSWORD": "initial-inspector-password",
        "INITIAL_INSPECTOR_FULL_NAME": "Initial Inspector",
        "INITIAL_STAFF_USERNAME": "first-staff",
        "INITIAL_STAFF_EMAIL": "first-staff@example.invalid",
        "INITIAL_STAFF_PASSWORD": "initial-staff-password",
        "INITIAL_STAFF_FULL_NAME": "Initial Staff",
    }

    create_app(config)
    config["INITIAL_INSPECTOR_PASSWORD"] = "different-inspector-password"
    config["INITIAL_STAFF_PASSWORD"] = "different-staff-password"
    app = create_app(config)

    with app.app_context():
        inspector = User.query.filter_by(username="first-inspector").one()
        staff = User.query.filter_by(username="first-staff").one()
        assert inspector.role == "inspector"
        assert check_password_hash(
            inspector.password_hash, "initial-inspector-password"
        )
        assert staff.role == "staff"
        assert check_password_hash(staff.password_hash, "initial-staff-password")


def test_initial_admin_rejects_short_password(tmp_path):
    with pytest.raises(ValueError, match="at least 12 characters"):
        create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-only-secret",
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'short.db'}",
                "SEED_DEMO_DATA": False,
                "INITIAL_ADMIN_USERNAME": "first-admin",
                "INITIAL_ADMIN_EMAIL": "first-admin@example.invalid",
                "INITIAL_ADMIN_PASSWORD": "short",
                "INITIAL_ADMIN_FULL_NAME": "Initial Admin",
            }
        )


def test_production_rejects_missing_or_weak_secret(tmp_path, monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "short")

    with pytest.raises(RuntimeError, match="at least 32 characters"):
        create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'production.db'}",
            }
        )
