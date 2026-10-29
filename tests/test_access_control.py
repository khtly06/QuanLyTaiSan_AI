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


def test_read_only_roles_do_not_see_unavailable_write_controls(client):
    _login(client, "test-staff")

    read_only_pages = (
        ("/assets", "Thêm tài sản mới", 'action="/assets"'),
        ("/inventory", "Tạo đợt kiểm kê mới", 'action="/inventory"'),
        ("/transfers", "Ghi nhận điều chuyển", 'action="/transfers"'),
        ("/repairs", "Gửi yêu cầu sửa chữa", 'action="/repairs"'),
        ("/disposals", "Ghi nhận thanh lý", 'action="/disposals"'),
        ("/categories", "Tạo danh mục mới", 'action="/categories"'),
        ("/departments", "Thêm phòng ban", 'action="/departments"'),
    )
    for path, unavailable_action, unavailable_form in read_only_pages:
        response = client.get(path)
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        assert unavailable_action not in page
        assert unavailable_form not in page

    for path, unavailable_controls in (
        ("/inventory", ("name=\"name\"", "Lưu đợt kiểm kê")),
        (
            "/transfers",
            ('name="from_department_id"', 'name="to_department_id"', "Lưu điều chuyển"),
        ),
        (
            "/repairs",
            ('name="request_date"', 'name="cost"', 'name="description"', "Gửi yêu cầu"),
        ),
        (
            "/disposals",
            ('name="disposal_date"', 'name="liquidation_value"', 'name="reason"', "Lưu hồ sơ"),
        ),
    ):
        page = client.get(path).get_data(as_text=True)
        for control in unavailable_controls:
            assert control not in page


def test_inspector_sees_only_inventory_write_controls(client):
    _login(client, "test-inspector")

    inventory_page = client.get("/inventory").get_data(as_text=True)
    assets_page = client.get("/assets").get_data(as_text=True)
    repairs_page = client.get("/repairs").get_data(as_text=True)

    assert "Tạo đợt kiểm kê mới" in inventory_page
    assert 'name="name"' in inventory_page
    assert "Lưu đợt kiểm kê" in inventory_page
    assert "Thêm tài sản mới" not in assets_page
    assert "Gửi yêu cầu sửa chữa" not in repairs_page
    assert 'name="request_date"' not in repairs_page
    assert "Gửi yêu cầu" not in repairs_page


def test_manager_can_generate_general_ai_report_but_not_admin_only_types(client):
    _login(client, "test-manager")

    response = client.get("/ai/report")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Tóm tắt tình trạng theo phòng ban" in page
    assert "Báo cáo kiểm kê" not in page
    assert "Gợi ý sửa chữa hoặc thay thế" not in page
    assert 'id="generate-report" type="button" disabled' not in page


def test_manager_cannot_toggle_user_accounts(app, client):
    _login(client, "test-manager")
    with app.app_context():
        target = User.query.filter_by(username="test-staff").one()
        target_id = target.id

    response = client.post(f"/users/{target_id}/toggle-active")

    assert response.status_code == 403
    with app.app_context():
        assert User.query.filter_by(username="test-staff").one().is_active


def test_staff_and_inspector_can_log_out(client):
    for username in ("test-staff", "test-inspector"):
        _login(client, username)
        response = client.post("/logout", follow_redirects=False)

        assert response.status_code == 302
        assert response.headers["Location"].endswith("/login")
        with client.session_transaction() as current_session:
            assert "user_id" not in current_session


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
