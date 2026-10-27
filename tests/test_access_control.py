"""Tests for role enforcement, inactive sessions, and CSRF."""

import re

from werkzeug.security import generate_password_hash

from app import create_app
from app.models import User, db


def _login(client, username):
    return client.post(
        "/login",
        data={"username": username, "password": "test-password-123"},
    )


def test_staff_is_read_only_and_admin_area_is_forbidden(app, client):
    _login(client, "test-staff")

    mutation = client.post(
        "/assets",
        data={
            "asset_code": "NO-ACCESS",
            "name": "Không được tạo",
            "category_id": "1",
            "department_id": "1",
        },
    )
    admin_page = client.get("/users")

    assert mutation.status_code == 403
    assert admin_page.status_code == 403
    with app.app_context():
        from app.models import Asset

        assert Asset.query.filter_by(asset_code="NO-ACCESS").first() is None


def test_inspector_can_record_inventory_but_cannot_mutate_assets(app, client):
    _login(client, "test-inspector")
    inventory = client.post(
        "/inventory",
        data={"name": "Đợt kiểm kê", "start_date": "2026-10-26"},
    )
    asset = client.post(
        "/assets",
        data={
            "asset_code": "NO-ACCESS",
            "name": "Không được tạo",
            "category_id": "1",
            "department_id": "1",
        },
    )

    assert inventory.status_code == 302
    assert asset.status_code == 403


def test_inactive_user_session_is_revoked(app, client):
    _login(client, "test-staff")
    with app.app_context():
        user = User.query.filter_by(username="test-staff").one()
        user.is_active = False
        db.session.commit()

    response = client.get("/profile", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
    with client.session_transaction() as current_session:
        assert "user_id" not in current_session


def test_csrf_blocks_missing_token_and_accepts_valid_login_token(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "csrf-test-secret",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'csrf.db'}",
            "SEED_DEMO_DATA": False,
        }
    )
    with app.app_context():
        db.session.add(
            User(
                username="csrf-user",
                email="csrf-user@example.invalid",
                full_name="CSRF User",
                role="staff",
                password_hash=generate_password_hash("test-password-123"),
            )
        )
        db.session.commit()

    client = app.test_client()
    rejected = client.post(
        "/login",
        data={"username": "csrf-user", "password": "test-password-123"},
    )
    page = client.get("/login").get_data(as_text=True)
    token_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page)
    assert token_match is not None
    accepted = client.post(
        "/login",
        data={
            "csrf_token": token_match.group(1),
            "username": "csrf-user",
            "password": "test-password-123",
        },
    )

    assert rejected.status_code == 400
    assert accepted.status_code == 302


def test_csrf_blocks_json_report_without_header(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "csrf-api-test-secret",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'csrf-api.db'}",
            "SEED_DEMO_DATA": False,
        }
    )
    with app.app_context():
        db.session.add(
            User(
                username="csrf-admin",
                email="csrf-admin@example.invalid",
                full_name="CSRF Admin",
                role="admin",
                password_hash=generate_password_hash("test-password-123"),
            )
        )
        db.session.commit()

    csrf_enabled = app.test_client()
    login_page = csrf_enabled.get("/login").get_data(as_text=True)
    token = re.search(
        r'name="csrf_token"[^>]*value="([^"]+)"', login_page
    ).group(1)
    csrf_enabled.post(
        "/login",
        data={
            "csrf_token": token,
            "username": "csrf-admin",
            "password": "test-password-123",
        },
    )
    page = csrf_enabled.get("/ai/report").get_data(as_text=True)
    header_token = re.search(r'<meta name="csrf-token" content="([^"]+)"', page).group(1)

    missing = csrf_enabled.post("/ai/report", json={"report_type": "overview"})
    accepted = csrf_enabled.post(
        "/ai/report",
        json={"report_type": "overview"},
        headers={"X-CSRFToken": header_token},
    )

    assert missing.status_code == 400
    assert accepted.status_code == 200
