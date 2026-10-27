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
    app, authenticated_client
):
    from app.models import Inventory

    authenticated_client.post(
        "/inventory",
        data={"name": "Kiểm kê AI", "start_date": "2026-10-26"},
    )
    with app.app_context():
        campaign_id = Inventory.query.one().id

    response = authenticated_client.post(
        "/ai/report",
        json={"report_type": "inventory", "inventory_id": campaign_id},
    )

    assert response.status_code == 200
    stats = response.get_json()["stats"]
    assert stats["expected_count"] == 1
    assert stats["checked_count"] == 0
    assert stats["unverified_count"] == 1
    assert stats["confirmed_missing_count"] == 0


def test_department_report_requires_and_scopes_department(
    app, authenticated_client
):
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
