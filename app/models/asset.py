"""Asset model for school assets."""

from app.models import db


class Asset(db.Model):
    """Represents an asset item."""

    __tablename__ = "assets"

    id = db.Column(db.Integer, primary_key=True)
    asset_code = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id"),
        nullable=False,
    )
    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id"),
        nullable=False,
    )
    user_name = db.Column(db.String(120), nullable=True)
    purchase_date = db.Column(db.Date, nullable=True)
    value = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(50), default="active")
    location = db.Column(db.String(200), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    category = db.relationship("Category", back_populates="assets")
    department = db.relationship("Department", back_populates="assets")
    repairs = db.relationship("Repair", back_populates="asset")
    disposals = db.relationship("Disposal", back_populates="asset")
    transfers = db.relationship("Transfer", back_populates="asset")

    def __repr__(self):
        """Return a readable representation for debugging."""
        return f"<Asset {self.asset_code}>"
