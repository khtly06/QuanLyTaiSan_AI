"""Report generation service."""


class ReportService:
    """Service for school asset and maintenance reporting."""

    def generate_asset_report(self):
        """Create an asset summary report."""
        return {
            "title": "Báo cáo tài sản",
            "data": [
                {"label": "Tổng số tài sản", "value": 120},
                {"label": "Đang sử dụng", "value": 96},
                {"label": "Đang sửa chữa", "value": 12},
            ],
        }

    def generate_department_report(self):
        """Create a department summary report."""
        return {
            "title": "Báo cáo theo phòng ban",
            "data": [
                {"label": "Ban Giám hiệu", "value": 18},
                {"label": "Khoa Công nghệ", "value": 42},
                {"label": "Phòng Kế toán", "value": 15},
            ],
        }
