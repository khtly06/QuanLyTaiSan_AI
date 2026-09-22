"""Department model."""

from app.models import db


class Department(db.Model):
    """School department model."""

    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    code = db.Column(db.String(40), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    assets = db.relationship("Asset", back_populates="department")
    transfer_from = db.relationship(
        "Transfer",
        foreign_keys="Transfer.from_department_id",
        back_populates="from_department",
    )
    transfer_to = db.relationship(
        "Transfer",
        foreign_keys="Transfer.to_department_id",
        back_populates="to_department",
    )

    def __repr__(self):
        """Return a readable representation for debugging."""
        return f"<Department {self.name}>"
