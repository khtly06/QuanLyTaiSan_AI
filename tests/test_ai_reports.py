"""Tests for database-grounded AI report prompt and response handling."""

import json


class FakeConfiguredLLM:
    def __init__(self, response):
        self.response = response

    def _has_valid_key(self):
        return True

    def generate(self, prompt, system_prompt=None):
        assert "Dữ liệu thống kê thực tế" in prompt
        assert "không tạo tài sản" in system_prompt.lower()
        return self.response


def test_ai_report_accepts_structured_json_from_service(
    authenticated_client, monkeypatch
):
    monkeypatch.setattr(
        "app.routes.ai._create_llm_service",
        lambda: FakeConfiguredLLM(
            json.dumps(
                {
                    "summary": "Có một tài sản.",
                    "observations": ["Tổng số là 1."],
                    "recommendations": ["Tiếp tục theo dõi."],
                },
                ensure_ascii=False,
            )
        ),
    )

    response = authenticated_client.post(
        "/ai/report", json={"report_type": "overview"}
    )

    assert response.status_code == 200
    result = response.get_json()
    assert json.loads(result["analysis"])["summary"] == "Có một tài sản."
    assert result["stats"]["total_assets"] == 1


def test_ai_report_does_not_display_malformed_model_output(
    authenticated_client, monkeypatch
):
    monkeypatch.setattr(
        "app.routes.ai._create_llm_service",
        lambda: FakeConfiguredLLM("not valid JSON"),
    )

    response = authenticated_client.post(
        "/ai/report", json={"report_type": "overview"}
    )

    assert response.status_code == 200
    analysis = response.get_json()["analysis"]
    assert "không thể tạo phân tích tự động" in analysis
    assert "not valid JSON" not in analysis


def test_inventory_report_uses_explicit_campaign_results(
    app, authenticated_client, monkeypatch
):
    from app.models import Inventory, InventoryDetail
    monkeypatch.setattr(
        "app.routes.ai._safe_llm_generate",
        lambda prompt, system_prompt=None: '{"summary":"Kiểm kê","observations":[],"recommendations":[]}',
    )

    authenticated_client.post(
        "/inventory",
        data={"name": "Kiểm kê AI", "start_date": "2026-10-26"},
    )
    with app.app_context():
        campaign_id = Inventory.query.one().id
        detail_id = InventoryDetail.query.one().id

    pending = authenticated_client.post(
        "/ai/report",
        json={"report_type": "inventory", "inventory_id": campaign_id},
    )
    assert pending.status_code == 400

    authenticated_client.post(
        f"/inventory/{campaign_id}",
        data={
            "detail_id": str(detail_id),
            "actual_status": "active",
            "actual_location": "Phòng A",
        },
    )
    authenticated_client.post(f"/inventory/{campaign_id}/complete")

    response = authenticated_client.post(
        "/ai/report",
        json={"report_type": "inventory", "inventory_id": campaign_id},
    )

    assert response.status_code == 200
    stats = response.get_json()["stats"]
    assert stats["expected_count"] == 1
    assert stats["checked_count"] == 1
    assert stats["unverified_count"] == 0
    assert stats["accounted_for_count"] == 1
    assert stats["wrong_location_count"] == 0
    assert stats["location_not_recorded_count"] == 1
    assert response.get_json()["reference_label"] == "Kết quả AI – Tham khảo"


def test_inventory_report_includes_location_and_issue_categories(
    app, authenticated_client, monkeypatch
):
    from app.models import Asset, Inventory, InventoryDetail, db
    monkeypatch.setattr(
        "app.routes.ai._safe_llm_generate",
        lambda prompt, system_prompt=None: '{"summary":"Kiểm kê","observations":[],"recommendations":[]}',
    )

    with app.app_context():
        asset = Asset.query.filter_by(asset_code="TEST-001").one()
        asset.location = "Phòng A"
        db.session.commit()

    authenticated_client.post(
        "/inventory",
        data={"name": "Kiểm kê vị trí", "start_date": "2026-10-26"},
    )
    with app.app_context():
        campaign = Inventory.query.one()
        detail = InventoryDetail.query.one()
        campaign_id = campaign.id
        detail_id = detail.id

    authenticated_client.post(
        f"/inventory/{campaign_id}",
        data={
            "detail_id": str(detail_id),
            "actual_status": "damaged",
            "actual_location": "Phòng B",
            "variance_note": "Thiết bị hỏng",
        },
    )
    authenticated_client.post(f"/inventory/{campaign_id}/complete")
    response = authenticated_client.post(
        "/ai/report",
        json={"report_type": "inventory", "inventory_id": campaign_id},
    )

    assert response.status_code == 200
    stats = response.get_json()["stats"]
    assert stats["accounted_for_count"] == 1
    assert stats["damaged_count"] == 1
    assert stats["wrong_location_count"] == 1
    assert stats["asset_results"][0]["classification"] == [
        "accounted_for",
        "damaged",
        "wrong_location",
        "status_mismatch",
    ]


def test_manager_cannot_generate_admin_only_ai_reports(
    client, app
):
    client.post(
        "/login",
        data={"username": "test-manager", "password": "test-password-123"},
    )
    response = client.post(
        "/ai/report",
        json={"report_type": "recommendations", "department_id": 1},
    )

    assert response.status_code == 403


def test_department_report_requires_and_scopes_department(
    app, authenticated_client, monkeypatch
):
    monkeypatch.setattr(
        "app.routes.ai._safe_llm_generate",
        lambda prompt, system_prompt=None: '{"summary":"Phòng ban","observations":[],"recommendations":[]}',
    )
    from app.models import Department

    with app.app_context():
        department_id = Department.query.filter_by(code="B").one().id

    missing = authenticated_client.post(
        "/ai/report", json={"report_type": "department"}
    )
    scoped = authenticated_client.post(
        "/ai/report",
        json={"report_type": "department", "department_id": department_id},
    )

    assert missing.status_code == 400
    assert scoped.status_code == 200
    assert scoped.get_json()["stats"]["department"] == "Phòng B"
    assert scoped.get_json()["stats"]["asset_count"] == 0
    assert scoped.get_json()["reference_label"] == "Tham khảo"


def test_department_report_counts_damage_and_pending_disposal(
    app, authenticated_client, monkeypatch
):
    from datetime import date

    from app.models import Asset, Department, Disposal, db

    captured = {}

    def fake_generate(prompt, system_prompt=None):
        captured["prompt"] = prompt
        return '{"summary":"Tóm tắt","observations":[],"recommendations":[]}'

    monkeypatch.setattr("app.routes.ai._safe_llm_generate", fake_generate)
    with app.app_context():
        department = Department.query.filter_by(code="A").one()
        asset = Asset.query.filter_by(asset_code="TEST-001").one()
        asset.status = "damaged"
        db.session.add(
            Disposal(
                asset_id=asset.id,
                disposal_date=date(2026, 10, 1),
                reason="Đang chờ duyệt",
                status="requested",
            )
        )
        db.session.commit()
        department_id = department.id

    response = authenticated_client.post(
        "/ai/report",
        json={"report_type": "department", "department_id": department_id},
    )

    assert response.status_code == 200
    stats = response.get_json()["stats"]
    assert stats["status_counts"] == {
        "in_use": 0,
        "damaged": 1,
        "under_repair": 0,
        "pending_disposal": 1,
    }
    assert stats["assets"][0]["pending_disposal"] is True
    assert "tổng số tài sản, đang sử dụng, hỏng, đang sửa và chờ thanh lý" in (
        captured["prompt"].casefold()
    )


def test_recommendations_data_includes_age_life_and_repair_history(app):
    from datetime import date

    from app.models import Asset, Repair, db
    from app.routes.ai import _report_stats

    with app.app_context():
        asset = Asset.query.filter_by(asset_code="TEST-001").one()
        asset.purchase_date = date(2020, 1, 1)
        asset.useful_life_years = 8
        db.session.add(
            Repair(
                asset_id=asset.id,
                request_date=date(2025, 1, 1),
                status="completed",
                description="Thay bộ nguồn",
                cost=100,
            )
        )
        db.session.commit()
        data = _report_stats(
            "recommendations",
            department_id=asset.department_id,
        )

    result = next(item for item in data["assets"] if item["asset_code"] == "TEST-001")
    assert result["age_years"] is not None
    assert result["useful_life_years"] == 8
    assert result["repair_count"] == 1
    assert result["repair_history"][0]["description"] == "Thay bộ nguồn"


def test_ai_reference_report_is_saved_and_admin_can_approve_it(
    app, authenticated_client, monkeypatch
):
    from app.models import AIReport, Department, db

    monkeypatch.setattr(
        "app.routes.ai._safe_llm_generate",
        lambda prompt, system_prompt=None: (
            '{"summary":"Tóm tắt phòng ban","observations":["Có một tài sản"],'
            '"recommendations":["Tiếp tục theo dõi"]}'
        ),
    )
    with app.app_context():
        department_id = Department.query.filter_by(code="A").one().id

    generated = authenticated_client.post(
        "/ai/report",
        json={"report_type": "department", "department_id": department_id},
    )
    report_id = generated.get_json()["report_id"]
    assert generated.status_code == 200
    assert report_id is not None
    assert generated.get_json()["review_status"] == "pending"

    saved = authenticated_client.get(f"/ai/report-records/{report_id}")
    assert saved.status_code == 200
    assert saved.get_json()["can_decide"] is True
    assert saved.get_json()["stats"]["department"] == "Phòng A"

    decision = authenticated_client.post(
        f"/ai/report-records/{report_id}/decision",
        json={"decision": "approved"},
    )
    assert decision.status_code == 200
    assert decision.get_json()["review_status"] == "approved"

    with app.app_context():
        report = db.session.get(AIReport, report_id)
        assert report.status == "approved"
        assert report.decided_by.username == "test-admin"
        assert report.decided_at is not None


def test_only_admin_can_decide_saved_ai_report(
    app, authenticated_client, client, monkeypatch
):
    from app.models import AIReport, Department, db

    monkeypatch.setattr(
        "app.routes.ai._safe_llm_generate",
        lambda prompt, system_prompt=None: (
            '{"summary":"Tóm tắt","observations":[],"recommendations":[]}'
        ),
    )
    with app.app_context():
        department_id = Department.query.filter_by(code="A").one().id
    generated = authenticated_client.post(
        "/ai/report",
        json={"report_type": "department", "department_id": department_id},
    )
    report_id = generated.get_json()["report_id"]

    client.post(
        "/login",
        data={"username": "test-manager", "password": "test-password-123"},
    )
    forbidden = client.post(
        f"/ai/report-records/{report_id}/decision",
        json={"decision": "rejected"},
    )
    assert forbidden.status_code == 403

    with app.app_context():
        report = db.session.get(AIReport, report_id)
        assert report.status == "pending"


def test_failed_ai_report_cannot_be_approved(
    app, authenticated_client, monkeypatch
):
    from app.models import AIReport, Department, db

    def fail_generation(prompt, system_prompt=None):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr("app.routes.ai._safe_llm_generate", fail_generation)
    with app.app_context():
        department_id = Department.query.filter_by(code="A").one().id

    generated = authenticated_client.post(
        "/ai/report",
        json={"report_type": "department", "department_id": department_id},
    )
    report_id = generated.get_json()["report_id"]
    assert generated.get_json()["review_status"] == "unavailable"
    decision = authenticated_client.post(
        f"/ai/report-records/{report_id}/decision",
        json={"decision": "approved"},
    )
    assert decision.status_code == 409
    with app.app_context():
        assert db.session.get(AIReport, report_id).status == "unavailable"
