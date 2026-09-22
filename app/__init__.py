"""Initialize the Flask application package."""

from pathlib import Path

from flask import Flask, session
from sqlalchemy import text
from werkzeug.security import generate_password_hash

from config import Config


def _ensure_seed_data(app):
    """Create the SQLite schema and seed data when the database is empty."""
    from app.models import Category, User, db

    database_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if database_uri.startswith("sqlite:///"):
        db_path = database_uri.replace("sqlite:///", "", 1)
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

    with app.app_context():
        db.create_all()

        inspector = db.inspect(db.engine)
        table_names = set(inspector.get_table_names())
        columns = []
        if "users" in table_names:
            columns = [column["name"] for column in inspector.get_columns("users")]

        if "is_active" not in columns:
            db.session.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1"))
            db.session.commit()

        default_users = {
            "admin": {
                "email": "admin@school.edu.vn",
                "password_hash": generate_password_hash("admin123"),
                "role": "admin",
                "full_name": "Admin",
                "is_active": True,
            },
            "staff01": {
                "email": "staff01@school.edu.vn",
                "password_hash": generate_password_hash("staff123"),
                "role": "staff",
                "full_name": "Nhân viên quản lý",
                "is_active": True,
            },
        }

        for username, payload in default_users.items():
            user = User.query.filter_by(username=username).first()
            if user is None:
                user = User(username=username, **payload)
                db.session.add(user)
            else:
                for field, value in payload.items():
                    setattr(user, field, value)

        db.session.commit()

        if Category.query.first() is None:
            seed_file = Path(app.root_path).resolve().parent / "database" / "seed.sql"
            if seed_file.exists():
                sql = seed_file.read_text(encoding="utf-8")
                for statement in [part.strip() for part in sql.split(";") if part.strip()]:
                    if "INSERT INTO users" in statement:
                        continue
                    db.session.execute(text(statement))
                db.session.commit()


def create_app():
    """Create and configure the app instance."""
    app = Flask(__name__)
    app.config.from_object(Config)

    from app.models import User, db

    db.init_app(app)
    _ensure_seed_data(app)

    @app.context_processor
    def inject_user():
        user = None
        user_id = session.get("user_id")
        if user_id:
            user = db.session.get(User, user_id)
        return {
            "current_user": user,
            "is_admin_user": bool(user and user.is_admin),
            "user_display_name": user.full_name if user and user.full_name else (user.username if user else "Khách"),
            "user_role_label": user.display_role if user else "Khách",
        }

    from app.routes import register_routes

    register_routes(app)

    return app
