"""Tests for physical inventory snapshots and recorded results."""

from datetime import date

from app.models import Inventory, InventoryDetail, db


def _login(client, username):
    client.post(
        "/login",
        data={"username": username, "password": "test-password-123"},
    )


def test_inventory_creation_snapshots_assets_without_marking_them_missing(
    app, client
):
    _login(client, "test-manager")
    with app.app_context():
        from app.models import Asset

        asset = Asset.query.one()
        asset.location = "Phòng A - Kệ 1"
        db.session.commit()
    response = client.post(
        "/inventory",
        data={"name": "Kiểm kê học kỳ", "start_date": "2026-10-26"},
    )

    assert response.status_code == 302
    with app.app_context():
        campaign = Inventory.query.one()
        detail = InventoryDetail.query.one()
        assert campaign.status == "pending"
        assert detail.expected_status == "active"
        assert detail.expected_location == "Phòng A - Kệ 1"
        assert detail.actual_status is None


def test_inventory_requires_explicit_count_before_completion(app, client):
    _login(client, "test-inspector")
    client.post(
        "/inventory",
        data={"name": "Kiểm kê", "start_date": "2026-10-26"},
    )
    with app.app_context():
        campaign_id = Inventory.query.one().id

    incomplete = client.post(f"/inventory/{campaign_id}/complete")
    assert incomplete.status_code == 400

    with app.app_context():
        detail_id = InventoryDetail.query.one().id
    recorded = client.post(
        f"/inventory/{campaign_id}",
        data={
            "detail_id": str(detail_id),
            "actual_status": "missing",
            "actual_location": "Phòng B",
            "variance_note": "Đã kiểm tra tại vị trí được phân công",
        },
    )
    assert recorded.status_code == 302

    completed = client.post(f"/inventory/{campaign_id}/complete")
    assert completed.status_code == 302
    with app.app_context():
        campaign = Inventory.query.one()
        detail = InventoryDetail.query.one()
        assert campaign.status == "completed"
        assert detail.actual_status == "missing"
        assert detail.actual_location == "Phòng B"
        assert detail.checked_by == "Test Inspector"
        assert detail.checked_at is not None
        assert campaign.end_date == date.today()


def test_inventory_records_unregistered_observation(app, client):
    _login(client, "test-inspector")
    client.post(
        "/inventory",
        data={"name": "Kiểm kê", "start_date": "2026-10-26"},
    )
    with app.app_context():
        campaign_id = Inventory.query.one().id

    response = client.post(
        f"/inventory/{campaign_id}/observations",
        data={
            "observed_code": "OBS-01",
            "observed_name": "Tài sản chưa ghi sổ",
            "actual_status": "active",
            "note": "Phát hiện trong phòng học",
        },
    )

    assert response.status_code == 302
    with app.app_context():
        observation = Inventory.query.one().observations[0]
        assert observation.observed_code == "OBS-01"
        assert observation.checked_by == "Test Inspector"
        assert observation.note == "Phát hiện trong phòng học"


def test_staff_cannot_create_inventory(client, app):
    _login(client, "test-staff")

    response = client.post(
        "/inventory",
        data={"name": "Không được phép", "start_date": "2026-10-26"},
    )

    assert response.status_code == 403
    with app.app_context():
        assert Inventory.query.count() == 0
