"""Disposal model."""

from app.models import db



class Disposal(db.Model):
    """Asset disposal record."""

    __tablename__ = "disposals"

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey("assets.id"), nullable=False)
    disposal_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    liquidation_value = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(50), default="requested")
    requested_by = db.Column(db.String(120), nullable=True)
    decided_by = db.Column(db.String(120), nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)

    asset = db.relationship("Asset", back_populates="disposals")

    def __repr__(self):
        """Return a readable representation for debugging."""
        return f"<Disposal {self.id}>"
