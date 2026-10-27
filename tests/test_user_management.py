"""Tests for administrator-controlled account provisioning and lockout."""

from app.models import User


def test_admin_creates_account_with_valid_role_and_hashed_password(
    app, authenticated_client
):
    response = authenticated_client.post(
        "/users",
        data={
            "full_name": "Kiểm kê viên",
            "username": "inspector-new",
            "email": "inspector-new@example.invalid",
            "role": "inspector",
            "password": "a-long-initial-password",
        },
    )

    assert response.status_code == 302
    with app.app_context():
        user = User.query.filter_by(username="inspector-new").one()
        assert user.role == "inspector"
        assert user.password_hash != "a-long-initial-password"


def test_user_management_rejects_short_password_and_invalid_role(
    app, authenticated_client
):
    short_password = authenticated_client.post(
        "/users",
        data={
            "full_name": "Người dùng",
            "username": "user-short",
            "email": "user-short@example.invalid",
            "role": "staff",
            "password": "short",
        },
    )
    invalid_role = authenticated_client.post(
        "/users",
        data={
            "full_name": "Người dùng",
            "username": "user-role",
            "email": "user-role@example.invalid",
            "role": "superuser",
            "password": "a-long-initial-password",
        },
    )

    assert short_password.status_code == 400
    assert invalid_role.status_code == 400
    with app.app_context():
        assert User.query.filter_by(username="user-short").first() is None
        assert User.query.filter_by(username="user-role").first() is None


def test_admin_cannot_lock_self_or_last_active_admin(app, authenticated_client):
    with app.app_context():
        admin_id = User.query.filter_by(username="test-admin").one().id
    self_lock = authenticated_client.post(f"/users/{admin_id}/toggle-active")
    last_admin_lock = authenticated_client.post(f"/users/{admin_id}/toggle-active")

    assert self_lock.status_code == 302
    assert last_admin_lock.status_code == 302
    with app.app_context():
        assert User.query.filter_by(username="test-admin").one().is_active
