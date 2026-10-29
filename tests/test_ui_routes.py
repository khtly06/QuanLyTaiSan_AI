"""UI route tests for the asset management dashboard and AI pages."""

import re

import requests

from app.models import Asset, Disposal, Inventory, Repair, db


def test_dashboard_page_renders_vietnamese_metrics(authenticated_client):
    """Dashboard page should render real metrics after a valid login session."""
    response = authenticated_client.get("/dashboard")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Tổng tài sản" in page
    assert "Tổng giá trị tài sản" in page
    assert "Thống kê tình trạng" in page
    assert "Cần chú ý" in page
    assert "Vị trí" in page


def test_asset_page_shows_status_donut_chart_and_total_value(authenticated_client):
    response = authenticated_client.get("/assets")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Phân bổ theo trạng thái" in page
    assert 'class="asset-donut"' in page
    assert "Đang sử dụng" in page
    assert "Đang sửa chữa" in page
    assert "Thanh lý" in page
    assert "Tổng giá trị tài sản" in page


def test_ai_chat_page_is_available(authenticated_client):
    """AI chat page should be accessible to logged-in users and not require direct LLM calls from the browser."""
    response = authenticated_client.get("/ai/chat")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Trợ lý AI" in page
    assert "Câu hỏi" in page


def test_ai_report_page_explains_reference_workflows_and_completed_inventory(
    app, authenticated_client
):
    from datetime import date

    from app.models import Inventory, db

    with app.app_context():
        db.session.add_all(
            [
                Inventory(
                    name="Đợt đang làm",
                    start_date=date(2026, 10, 1),
                    status="pending",
                ),
                Inventory(
                    name="Đợt đã xong",
                    start_date=date(2026, 9, 1),
                    status="completed",
                ),
            ]
        )
        db.session.commit()

    response = authenticated_client.get("/ai/report")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Kết quả AI – Tham khảo" in page
    assert "Tóm tắt tình trạng theo phòng ban" in page
    assert "Gợi ý sửa chữa hoặc thay thế" in page
    assert "Đợt đã xong" in page
    assert "Đợt đang làm" not in page


def test_ai_chat_returns_answer_when_provider_is_configured(
    app, authenticated_client, monkeypatch
):
    captured_request = {}
    app.config["LLM_API_KEY"] = "configured-test-key"

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": "Tài sản cần được kiểm kê mỗi quý."
                        }
                    }
                ]
            }

    def fake_post(url, **kwargs):
        captured_request["url"] = url
        captured_request.update(kwargs)
        return FakeResponse()

    monkeypatch.setattr("app.llm.llm_service.requests.post", fake_post)

    response = authenticated_client.post(
        "/ai/chat",
        json={"question": "Tần suất kiểm kê tài sản là bao lâu?"},
    )

    assert response.status_code == 200
    result = response.get_json()
    assert result["answer"] == "Tài sản cần được kiểm kê mỗi quý."
    assert "school_asset_policy.md" in result["sources"]
    assert captured_request["headers"]["Authorization"] == (
        "Bearer configured-test-key"
    )
    assert captured_request["timeout"] == app.config["LLM_TIMEOUT_SECONDS"]


def test_ai_chat_explains_provider_quota_error(
    app, authenticated_client, monkeypatch
):
    app.config["LLM_API_KEY"] = "configured-test-key"

    class FakeResponse:
        status_code = 429

        def raise_for_status(self):
            error = requests.HTTPError("provider quota error")
            error.response = self
            raise error

        def json(self):
            return {
                "error": {
                    "type": "insufficient_quota",
                    "code": "credit_balance_exhausted",
                    "message": "Do not expose this provider detail.",
                }
            }

    monkeypatch.setattr(
        "app.llm.llm_service.requests.post",
        lambda *args, **kwargs: FakeResponse(),
    )

    response = authenticated_client.post(
        "/ai/chat",
        json={"question": "Tần suất kiểm kê tài sản là bao lâu?"},
    )

    assert response.status_code == 503
    message = response.get_json()["message"]
    assert "hết hạn mức" in message
    assert "Do not expose" not in message


def test_ai_report_page_has_statistical_and_analysis_sections(authenticated_client):
    """AI report page should separate data and AI analysis clearly for authenticated users."""
    response = authenticated_client.get("/ai/report")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Dữ liệu thống kê" in page
    assert "Phân tích của AI" in page


def test_system_settings_show_provider_without_exposing_api_key(
    app, authenticated_client
):
    app.config["LLM_API_KEY"] = "test-secret-gemini-key"

    response = authenticated_client.get("/settings")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Nhà cung cấp" in page
    assert "Đã cấu hình" in page
    assert "test-secret-gemini-key" not in page
    assert "Lưu thay đổi" not in page


def test_ai_report_uses_local_provider_without_api_key(
    app, authenticated_client, monkeypatch
):
    app.config["LLM_API_BASE_URL"] = "http://localhost:11434/v1/chat/completions"

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"summary":"Tóm tắt","observations":[],'
                                '"recommendations":[]}'
                            )
                        }
                    }
                ]
            }

    monkeypatch.setattr(
        "app.llm.llm_service.requests.post",
        lambda *args, **kwargs: FakeResponse(),
    )
    response = authenticated_client.post(
        "/ai/report", json={"report_type": "overview"}
    )

    assert response.status_code == 200
    result = response.get_json()
    assert result["stats"]["total_assets"] == 1
    assert '"summary": "Tóm tắt"' in result["analysis"]


def test_ai_report_rejects_unknown_report_type(authenticated_client):
    response = authenticated_client.post(
        "/ai/report", json={"report_type": "unknown"}
    )

    assert response.status_code == 400


def test_reports_count_assets_with_the_disposal_status(
    app, authenticated_client
):
    with app.app_context():
        asset = Asset.query.filter_by(asset_code="TEST-001").one()
        asset.status = "disposal"
        db.session.commit()

    response = authenticated_client.get("/reports")
    page = response.get_data(as_text=True)
    match = re.search(
        r'<div class="metric-label">Đã thanh lý</div>\s*'
        r'<p class="metric-value">([^<]+)</p>',
        page,
    )

    assert response.status_code == 200
    assert match is not None
    assert match.group(1) == "1"


def test_reports_render_department_and_category_tables(authenticated_client):
    response = authenticated_client.get("/reports")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "<th>Phòng ban</th>" in page
    assert "<th>Loại tài sản</th>" in page
    assert "<th>Giá trị</th>" in page
    assert "<td>Phòng A</td>" in page
    assert "Thiết bị" in page
    assert "report-column-chart" not in page


def test_reports_translate_workflow_statuses_and_count_active_repairs(
    app, authenticated_client
):
    from datetime import date

    with app.app_context():
        asset = Asset.query.filter_by(asset_code="TEST-001").one()
        db.session.add_all(
            [
                Repair(
                    asset_id=asset.id,
                    request_date=date(2026, 10, 1),
                    status="pending",
                    description="Chờ xử lý",
                ),
                Repair(
                    asset_id=asset.id,
                    request_date=date(2026, 10, 2),
                    status="in_progress",
                    description="Đang xử lý",
                ),
                Repair(
                    asset_id=asset.id,
                    request_date=date(2026, 10, 3),
                    status="completed",
                    description="Đã xong",
                ),
                Disposal(
                    asset_id=asset.id,
                    disposal_date=date(2026, 10, 4),
                    reason="Chờ duyệt",
                    status="requested",
                ),
                Disposal(
                    asset_id=asset.id,
                    disposal_date=date(2026, 10, 5),
                    reason="Đã duyệt",
                    status="approved",
                ),
                Disposal(
                    asset_id=asset.id,
                    disposal_date=date(2026, 10, 6),
                    reason="Từ chối",
                    status="rejected",
                ),
                Inventory(
                    name="Đang thực hiện",
                    start_date=date(2026, 10, 7),
                    status="pending",
                ),
                Inventory(
                    name="Hoàn thành",
                    start_date=date(2026, 10, 8),
                    status="completed",
                ),
            ]
        )
        db.session.commit()

    response = authenticated_client.get("/reports")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Chờ xử lý" in page
    assert "Đang sửa chữa" in page
    assert "Hoàn thành" in page
    assert "Chờ duyệt" in page
    assert "Đã duyệt" in page
    assert "Từ chối" in page
    assert "Đang thực hiện" in page
    assert "status-{{" not in page


def test_login_page_renders_and_session_can_login(client):
    """The login page should be available and accept real credential-based login."""
    page = client.get("/login")
    assert page.status_code == 200
    assert "ĐĂNG NHẬP" in page.get_data(as_text=True)

    login = client.post(
        "/login",
        data={"username": "test-admin", "password": "test-password-123"},
        follow_redirects=False,
    )
    assert login.status_code == 302

    profile = client.get("/profile")
    assert profile.status_code == 200
    page_text = profile.get_data(as_text=True)
    assert "Test Admin" in page_text or "Quản trị viên" in page_text


def test_protected_routes_redirect_to_login_when_not_authenticated(client):
    """Unauthenticated users must not access dashboard and asset routes directly."""
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_health_endpoint_checks_database_without_authentication(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_login_rejects_invalid_password(client):
    response = client.post(
        "/login",
        data={"username": "test-admin", "password": "wrong-password"},
    )

    assert response.status_code == 401
