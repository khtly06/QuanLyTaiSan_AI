"""Tests for requested and approved asset disposal."""

from datetime import date

from app.models import Asset, Disposal, db


def _login(client, username):
    client.post(
        "/login",
        data={"username": username, "password": "test-password-123"},
    )


def test_disposal_request_requires_admin_decision_before_asset_is_disposed(
    app, client
):
    _login(client, "test-manager")
    created = client.post(
        "/disposals",
        data={
            "asset_id": "1",
            "disposal_date": "2026-10-26",
            "reason": "Thiết bị hết khả năng sử dụng",
            "liquidation_value": "100",
            "status": "approved",
        },
    )
    assert created.status_code == 302
    with app.app_context():
        disposal = Disposal.query.one()
        assert disposal.status == "requested"
        disposal_id = disposal.id
        assert Asset.query.one().status == "active"

    client.post("/logout")
    _login(client, "test-admin")
    approved = client.post(
        f"/disposals/{disposal_id}/decision",
        data={"decision": "approved"},
    )

    assert approved.status_code == 302
    with app.app_context():
        disposal = Disposal.query.one()
        assert disposal.status == "approved"
        assert disposal.decided_by == "Test Admin"
        assert disposal.decided_at is not None
        assert Asset.query.one().status == "disposal"


def test_non_admin_cannot_approve_disposal(app, client):
    with app.app_context():
        disposal = Disposal(
            asset_id=1,
            disposal_date=date(2026, 10, 26),
            reason="Chờ duyệt",
            status="requested",
        )
        db.session.add(disposal)
        db.session.commit()
        disposal_id = disposal.id
    _login(client, "test-manager")

    response = client.post(
        f"/disposals/{disposal_id}/decision",
        data={"decision": "approved"},
    )

    assert response.status_code == 403
    with app.app_context():
        assert Disposal.query.one().status == "requested"
        assert Asset.query.one().status == "active"


def test_pending_disposal_blocks_asset_transfer(client):
    _login(client, "test-manager")
    client.post(
        "/disposals",
        data={
            "asset_id": "1",
            "disposal_date": "2026-10-26",
            "reason": "Chờ duyệt",
            "liquidation_value": "0",
        },
    )

    response = client.post(
        "/transfers",
        data={
            "asset_id": "1",
            "from_department_id": "1",
            "to_department_id": "2",
            "transfer_date": "2026-10-26",
        },
    )

    assert response.status_code == 400
