"""Repair and maintenance model."""

from app.models import db


class Repair(db.Model):
    """Maintenance request record."""

    __tablename__ = "repairs"

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey("assets.id"), nullable=False)
    request_date = db.Column(db.Date, nullable=False)
    repair_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(50), default="pending")
    description = db.Column(db.Text, nullable=False)
    cost = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text, nullable=True)

    asset = db.relationship("Asset", back_populates="repairs")

    def __repr__(self):
        """Return a readable representation for debugging."""
        return f"<Repair {self.id}>"
