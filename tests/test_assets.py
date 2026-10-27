"""Tests for asset management functionality."""

from app.models import Asset


def _asset_form(**overrides):
    form = {
        "asset_code": "TEST-002",
        "name": "Máy chiếu mới",
        "category_id": "1",
        "department_id": "1",
        "value": "2500000",
        "status": "active",
    }
    form.update(overrides)
    return form


def test_asset_creation_persists_valid_data(app, authenticated_client):
    response = authenticated_client.post("/assets", data=_asset_form())

    assert response.status_code == 302
    with app.app_context():
        asset = Asset.query.filter_by(asset_code="TEST-002").one()
        assert asset.name == "Máy chiếu mới"
        assert asset.value == 2500000


def test_asset_creation_rejects_duplicate_code(app, authenticated_client):
    response = authenticated_client.post(
        "/assets", data=_asset_form(asset_code="TEST-001")
    )

    assert response.status_code == 302
    with app.app_context():
        assert Asset.query.filter_by(asset_code="TEST-001").count() == 1


def test_asset_creation_rejects_negative_value(app, authenticated_client):
    response = authenticated_client.post("/assets", data=_asset_form(value="-1"))

    assert response.status_code == 302
    with app.app_context():
        assert Asset.query.filter_by(asset_code="TEST-002").first() is None


def test_asset_creation_rejects_invalid_date_and_non_finite_value(
    app, authenticated_client
):
    invalid_date = authenticated_client.post(
        "/assets", data=_asset_form(purchase_date="not-a-date")
    )
    infinite_value = authenticated_client.post(
        "/assets", data=_asset_form(value="Infinity")
    )

    assert invalid_date.status_code == 302
    assert infinite_value.status_code == 302
    with app.app_context():
        assert Asset.query.filter_by(asset_code="TEST-002").first() is None


def test_asset_search_returns_matching_record(authenticated_client):
    response = authenticated_client.get("/assets?q=TEST-001")

    assert response.status_code == 200
    assert b"TEST-001" in response.data
