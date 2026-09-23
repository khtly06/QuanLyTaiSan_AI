"""Inventory service layer."""


class InventoryService:
    """Service for inventory rounds and variance tracking."""

    def create_inventory_round(self, name, start_date, end_date=None):
        """Create a new inventory round."""
        if not name or not start_date:
            raise ValueError("Inventory name and start date are required.")

        return {
            "name": name,
            "start_date": start_date,
            "end_date": end_date,
            "status": "pending",
        }

    def get_inventory_summary(self):
        """Return inventory summary details."""
        return {
            "total": 15,
            "pending": 4,
            "completed": 11,
            "variance": 2,
        }
