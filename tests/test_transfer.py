"""Tests for transfer validation, history, and current asset location."""

from app.models import Asset, Transfer, db


def _transfer_form(**overrides):
    form = {
        "asset_id": "1",
        "from_department_id": "1",
        "to_department_id": "2",
        "transfer_date": "2026-10-26",
        "reason": "Điều chỉnh phân bổ",
    }
    form.update(overrides)
    return form


def test_transfer_updates_asset_department_and_records_history(
    app, authenticated_client
):
    response = authenticated_client.post("/transfers", data=_transfer_form())

    assert response.status_code == 302
    with app.app_context():
        asset = Asset.query.filter_by(asset_code="TEST-001").one()
        transfer = Transfer.query.one()
        assert asset.department_id == 2
        assert transfer.from_department_id == 1
        assert transfer.to_department_id == 2
        assert transfer.reason == "Điều chỉnh phân bổ"


def test_transfer_rejects_incorrect_source_department(app, authenticated_client):
    response = authenticated_client.post(
        "/transfers",
        data=_transfer_form(from_department_id="2", to_department_id="1"),
    )

    assert response.status_code == 400
    assert "không khớp" in response.get_data(as_text=True)
    with app.app_context():
        assert Transfer.query.count() == 0
        assert Asset.query.filter_by(asset_code="TEST-001").one().department_id == 1


def test_transfer_rejects_non_active_asset(app, authenticated_client):
    with app.app_context():
        asset = Asset.query.filter_by(asset_code="TEST-001").one()
        asset.status = "disposal"
        db.session.commit()

    response = authenticated_client.post("/transfers", data=_transfer_form())

    assert response.status_code == 400
    assert "đang sử dụng" in response.get_data(as_text=True)
    with app.app_context():
        assert Transfer.query.count() == 0


def test_transfer_rejects_invalid_ids_without_server_error(authenticated_client):
    response = authenticated_client.post(
        "/transfers", data=_transfer_form(asset_id="not-an-id")
    )

    assert response.status_code == 400
