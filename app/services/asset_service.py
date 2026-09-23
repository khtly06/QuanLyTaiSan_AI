"""Asset service layer."""


class AssetService:
    """Service class for asset operations."""

    def __init__(self):
        self._assets = [
            {
                "id": 1,
                "asset_code": "TS-001",
                "name": "Laptop Dell Latitude",
                "category_id": 1,
                "department_id": 2,
                "user_name": "Nguyễn Văn A",
                "purchase_date": "2024-01-15",
                "value": 24000000,
                "status": "active",
                "location": "Phòng máy 2",
                "notes": "Laptop chính thức của phòng khoa",
            },
            {
                "id": 2,
                "asset_code": "TS-002",
                "name": "Máy in Canon",
                "category_id": 2,
                "department_id": 3,
                "user_name": "Trần Thị B",
                "purchase_date": "2023-10-20",
                "value": 8500000,
                "status": "active",
                "location": "Phòng kế toán",
                "notes": "Máy in cho văn phòng",
            },
            {
                "id": 3,
                "asset_code": "TS-003",
                "name": "Bàn ghế giáo viên",
                "category_id": 2,
                "department_id": 1,
                "user_name": "Lê Văn C",
                "purchase_date": "2022-08-05",
                "value": 12000000,
                "status": "repair",
                "location": "Phòng hiệu trưởng",
                "notes": "Cần thay mới ghế",
            },
        ]

    def get_total_assets(self):
        """Return total number of assets."""
        return len(self._assets)

    def get_dashboard_summary(self):
        """Return dashboard summary metrics."""
        total = self.get_total_assets()
        active = sum(1 for asset in self._assets if asset["status"] == "active")
        repair = sum(1 for asset in self._assets if asset["status"] == "repair")
        disposal = sum(1 for asset in self._assets if asset["status"] == "disposal")
        total_value = sum(float(asset["value"]) for asset in self._assets)

        return {
            "total_assets": total,
            "active_assets": active,
            "repair_assets": repair,
            "disposal_assets": disposal,
            "total_value": total_value,
            "chart": {
                "labels": ["Máy tính", "Thiết bị văn phòng", "Thiết bị khác"],
                "data": [40, 35, 25],
            },
        }

    def search_assets(
        self,
        query=None,
        category_id=None,
        department_id=None,
        status=None,
    ):
        """Search assets with filters."""
        filtered_assets = self._assets

        if query:
            query = query.lower()
            filtered_assets = [
                asset for asset in filtered_assets
                if any(query in asset["name"].lower() or query in asset["asset_code"].lower())
            ]

        if category_id:
            filtered_assets = [
                asset for asset in filtered_assets
                if str(asset["category_id"]) == str(category_id)
            ]

        if department_id:
            filtered_assets = [
                asset for asset in filtered_assets
                if str(asset["department_id"]) == str(department_id)
            ]

        if status:
            filtered_assets = [
                asset for asset in filtered_assets
                if asset["status"] == status
            ]

        return filtered_assets

    def create_asset(self, payload):
        """Create a new asset record."""
        required_fields = ["asset_code", "name", "category_id", "department_id"]
        missing = [field for field in required_fields if not payload.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        asset = {
            "id": max((item["id"] for item in self._assets), default=0) + 1,
            "asset_code": payload["asset_code"],
            "name": payload["name"],
            "category_id": payload["category_id"],
            "department_id": payload["department_id"],
            "user_name": payload.get("user_name"),
            "purchase_date": payload.get("purchase_date"),
            "value": float(payload.get("value", 0.0)),
            "status": payload.get("status", "active"),
            "location": payload.get("location"),
            "notes": payload.get("notes"),
        }
        self._assets.append(asset)
        return asset

    def get_asset_by_id(self, asset_id):
        """Return a single asset by identifier."""
        for asset in self._assets:
            if asset["id"] == asset_id:
                return asset
        return None

    def update_asset(self, asset_id, payload):
        """Update an asset record."""
        asset = self.get_asset_by_id(asset_id)
        if asset is None:
            return None

        for key, value in payload.items():
            if value is not None:
                asset[key] = value
        return asset

    def delete_asset(self, asset_id):
        """Delete an asset record."""
        for index, asset in enumerate(self._assets):
            if asset["id"] == asset_id:
                del self._assets[index]
                return True
        return False
