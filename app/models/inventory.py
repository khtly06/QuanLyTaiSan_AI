"""Inventory-related models."""

from app.models import db


class Inventory(db.Model):
    """Inventory round."""

    __tablename__ = "inventory"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(50), default="pending")

    details = db.relationship("InventoryDetail", back_populates="inventory")

    def __repr__(self):
        """Return a readable representation for debugging."""
        return f"<Inventory {self.name}>"


class InventoryDetail(db.Model):
    """Asset detail in an inventory round."""

    __tablename__ = "inventory_details"

    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(
        db.Integer,
        db.ForeignKey("inventory.id"),
        nullable=False,
    )
    asset_id = db.Column(db.Integer, db.ForeignKey("assets.id"), nullable=False)
    expected_status = db.Column(db.String(50), nullable=True)
    actual_status = db.Column(db.String(50), nullable=True)
    variance_note = db.Column(db.Text, nullable=True)

    inventory = db.relationship("Inventory", back_populates="details")
    asset = db.relationship("Asset")

    def __repr__(self):
        """Return a readable representation for debugging."""
        return f"<InventoryDetail {self.id}>"
