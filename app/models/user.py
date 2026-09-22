"""User model for the school asset management system."""

from app.models import db


class User(db.Model):
    """Represents an application user."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="staff")
    full_name = db.Column(db.String(120), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        """Return a readable representation for debugging."""
        return f"<User {self.username}>"

    @property
    def is_admin(self):
        """Return whether the user has administration permissions."""
        return self.role == "admin"

    @property
    def display_role(self):
        """Return the role label for the UI."""
        return "Quản trị viên" if self.role == "admin" else "Nhân viên"
