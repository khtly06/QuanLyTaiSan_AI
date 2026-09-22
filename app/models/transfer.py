"""Transfer model."""

from app.models import db


class Transfer(db.Model):
    """Asset transfer history."""

    __tablename__ = "transfers"

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey("assets.id"), nullable=False)
    from_department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id"),
        nullable=False,
    )
    to_department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id"),
        nullable=False,
    )
    transfer_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    asset = db.relationship("Asset", back_populates="transfers")
    from_department = db.relationship(
        "Department",
        foreign_keys="[Transfer.from_department_id]",
        back_populates="transfer_from",
    )
    to_department = db.relationship(
        "Department",
        foreign_keys="[Transfer.to_department_id]",
        back_populates="transfer_to",
    )

    def __repr__(self):
        """Return a readable representation for debugging."""
        return f"<Transfer {self.id}>"
