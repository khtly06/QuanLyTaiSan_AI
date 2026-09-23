"""UI route tests for the asset management dashboard and AI pages."""

from app import create_app


def test_dashboard_page_renders_vietnamese_metrics():
    """Dashboard page should render real metrics after a valid login session."""
    app = create_app()
    with app.test_client() as client:
        client.post("/login", data={"username": "admin", "password": "admin123"}, follow_redirects=False)
        response = client.get("/dashboard")
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        assert "Tổng số tài sản" in page
        assert "Tổng giá trị tài sản" in page


def test_ai_chat_page_is_available():
    """AI chat page should be accessible to logged-in users and not require direct LLM calls from the browser."""
    app = create_app()
    with app.test_client() as client:
        client.post("/login", data={"username": "admin", "password": "admin123"}, follow_redirects=False)
        response = client.get("/ai/chat")
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        assert "Trợ lý AI" in page
        assert "Câu hỏi" in page


def test_ai_report_page_has_statistical_and_analysis_sections():
    """AI report page should separate data and AI analysis clearly for authenticated users."""
    app = create_app()
    with app.test_client() as client:
        client.post("/login", data={"username": "admin", "password": "admin123"}, follow_redirects=False)
        response = client.get("/ai/report")
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        assert "DỮ LIỆU THỐNG KÊ" in page
        assert "PHÂN TÍCH CỦA AI" in page


def test_login_page_renders_and_session_can_login():
    """The login page should be available and accept real credential-based login."""
    app = create_app()
    with app.test_client() as client:
        page = client.get("/login")
        assert page.status_code == 200
        assert "ĐĂNG NHẬP" in page.get_data(as_text=True)

        login = client.post(
            "/login",
            data={"username": "admin", "password": "admin123"},
            follow_redirects=False,
        )
        assert login.status_code in {200, 302}

        profile = client.get("/profile")
        assert profile.status_code == 200
        page_text = profile.get_data(as_text=True)
        assert "Admin" in page_text or "Quản trị viên" in page_text


def test_protected_routes_redirect_to_login_when_not_authenticated():
    """Unauthenticated users must not access dashboard and asset routes directly."""
    app = create_app()
    with app.test_client() as client:
        response = client.get("/dashboard", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/login")
