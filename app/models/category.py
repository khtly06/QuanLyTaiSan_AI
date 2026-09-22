"""Category model."""

from app.models import db


class Category(db.Model):
    """Asset category."""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    assets = db.relationship("Asset", back_populates="category")

    def __repr__(self):
        """Return a readable representation for debugging."""
        return f"<Category {self.name}>"
