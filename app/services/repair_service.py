"""Repair service layer."""


class RepairService:
    """Service for repair requests and maintenance updates."""

    def create_repair_request(self, asset_id, description, cost=0.0):
        """Create a repair request."""
        if not asset_id or not description:
            raise ValueError("Asset id and description are required.")

        return {
            "asset_id": asset_id,
            "description": description,
            "cost": cost,
            "status": "pending",
        }

    def update_repair_status(self, repair_id, status):
        """Update repair status."""
        if not repair_id or not status:
            raise ValueError("Repair id and status are required.")

        return {"repair_id": repair_id, "status": status}
