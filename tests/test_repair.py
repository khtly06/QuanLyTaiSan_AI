"""Tests for repair request lifecycle and asset state synchronization."""

from app.models import Asset, Repair


def _login(client, username="test-manager"):
    client.post(
        "/login",
        data={"username": username, "password": "test-password-123"},
    )


def test_repair_lifecycle_updates_asset_status(app, client):
    _login(client)
    created = client.post(
        "/repairs",
        data={
            "asset_id": "1",
            "request_date": "2026-10-26",
            "description": "Màn hình chập chờn",
            "cost": "200000",
            "status": "completed",
        },
    )
    assert created.status_code == 302
    with app.app_context():
        repair = Repair.query.one()
        assert repair.status == "pending"
        assert repair.requested_by == "Test Manager"
        repair_id = repair.id
        assert Asset.query.one().status == "repair"

    started = client.post(
        f"/repairs/{repair_id}/update",
        data={"status": "in_progress", "cost": "210000"},
    )
    assert started.status_code == 302

    completed_without_date = client.post(
        f"/repairs/{repair_id}/update",
        data={"status": "completed", "cost": "210000"},
    )
    assert completed_without_date.status_code == 400

    completed = client.post(
        f"/repairs/{repair_id}/update",
        data={
            "status": "completed",
            "repair_date": "2026-10-27",
            "cost": "210000",
        },
    )
    assert completed.status_code == 302
    with app.app_context():
        repair = Repair.query.one()
        assert repair.status == "completed"
        assert repair.cost == 210000
        assert Asset.query.one().status == "active"


def test_repair_rejects_duplicate_open_request(app, client):
    _login(client)
    form = {
        "asset_id": "1",
        "request_date": "2026-10-26",
        "description": "Sự cố",
        "cost": "0",
    }
    assert client.post("/repairs", data=form).status_code == 302
    response = client.post("/repairs", data=form)

    assert response.status_code == 400
    with app.app_context():
        assert Repair.query.count() == 1


def test_staff_cannot_update_repair(client, app):
    _login(client)
    client.post(
        "/repairs",
        data={
            "asset_id": "1",
            "request_date": "2026-10-26",
            "description": "Sự cố",
        },
    )
    with app.app_context():
        repair_id = Repair.query.one().id
    client.post("/logout")
    _login(client, "test-staff")

    response = client.post(
        f"/repairs/{repair_id}/update", data={"status": "completed"}
    )

    assert response.status_code == 403
    with app.app_context():
        assert Repair.query.one().status == "pending"
