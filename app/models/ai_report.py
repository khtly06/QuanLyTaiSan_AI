"""Persist AI-generated reference reports and administrator review decisions."""

from datetime import UTC, datetime

from app.models import db


class AIReport(db.Model):
    """A generated AI report retained for review and audit."""

    __tablename__ = "ai_reports"

    id = db.Column(db.Integer, primary_key=True)
    report_type = db.Column(db.String(40), nullable=False)
    scope_label = db.Column(db.String(200), nullable=False)
    stats_json = db.Column(db.Text, nullable=False)
    analysis = db.Column(db.Text, nullable=False)
    reference_label = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="pending")
    ai_generated = db.Column(db.Boolean, nullable=False, default=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    decided_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
    )
    decided_at = db.Column(db.DateTime, nullable=True)

    created_by = db.relationship("User", foreign_keys=[created_by_id])
    decided_by = db.relationship("User", foreign_keys=[decided_by_id])

    def __repr__(self):
        return f"<AIReport {self.id} {self.report_type} {self.status}>"
