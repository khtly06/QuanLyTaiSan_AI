"""Initialize the Flask application package."""

from pathlib import Path
import os

from flask import Flask, abort, jsonify, redirect, request, session, url_for
from flask_wtf.csrf import CSRFError, CSRFProtect
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from werkzeug.security import generate_password_hash

from config import Config

csrf = CSRFProtect()


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(connection, _record):
    if connection.__class__.__module__.startswith("sqlite3"):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def _ensure_seed_data(app):
    """Create the schema and optionally provision users or demo data."""
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

        timestamp_type = (
            "DATETIME"
            if db.engine.dialect.name in {"sqlite", "mysql"}
            else "TIMESTAMP"
        )
        additive_columns = {
            "assets": {"useful_life_years": "INTEGER"},
            "inventory": {"created_by": "VARCHAR(120)"},
            "transfers": {"performed_by": "VARCHAR(120)"},
            "inventory_details": {
                "expected_location": "VARCHAR(200)",
                "actual_location": "VARCHAR(200)",
                "checked_by": "VARCHAR(120)",
                "checked_at": timestamp_type,
            },
            "repairs": {
                "requested_by": "VARCHAR(120)",
                "updated_by": "VARCHAR(120)",
            },
            "disposals": {
                "requested_by": "VARCHAR(120)",
                "decided_by": "VARCHAR(120)",
                "decided_at": timestamp_type,
            },
        }
        for table, additions in additive_columns.items():
            if table not in table_names:
                continue
            existing_columns = {
                column["name"] for column in db.inspect(db.engine).get_columns(table)
            }
            for column, sql_type in additions.items():
                if column not in existing_columns:
                    db.session.execute(
                        text(
                            f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}"
                        )
                    )
            db.session.commit()

        initial_users = {
            "admin": ("INITIAL_ADMIN", "administrator"),
            "inspector": ("INITIAL_INSPECTOR", "inspector"),
            "staff": ("INITIAL_STAFF", "staff"),
        }
        for role, (prefix, role_label) in initial_users.items():
            fields = {
                name: app.config.get(f"{prefix}_{name.upper()}", "")
                for name in ("username", "email", "password", "full_name")
            }
            if not any(fields.values()):
                continue
            if not all(fields.values()):
                raise ValueError(
                    f"All {prefix}_USERNAME, {prefix}_EMAIL, {prefix}_PASSWORD, "
                    f"and {prefix}_FULL_NAME values must be set to provision "
                    f"the initial {role_label}."
                )
            if len(fields["password"]) < 12:
                raise ValueError(
                    f"{prefix}_PASSWORD must contain at least 12 characters."
                )
            if User.query.filter_by(username=fields["username"]).first() is None:
                db.session.add(
                    User(
                        username=fields["username"],
                        email=fields["email"],
                        password_hash=generate_password_hash(fields["password"]),
                        role=role,
                        full_name=fields["full_name"],
                        is_active=True,
                    )
                )
                db.session.commit()

        if app.config.get("SEED_DEMO_DATA") and Category.query.first() is None:
            seed_file = Path(app.root_path).resolve().parent / "database" / "seed.sql"
            if seed_file.exists():
                sql = seed_file.read_text(encoding="utf-8")
                for statement in [part.strip() for part in sql.split(";") if part.strip()]:
                    if "INSERT INTO users" in statement:
                        continue
                    db.session.execute(text(statement))
                db.session.commit()


def create_app(test_config=None):
    """Create and configure the app instance."""
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    from app.models import User, db

    if os.environ.get("FLASK_ENV", "").strip().lower() == "production":
        configured_secret = os.getenv("SECRET_KEY", "")
        if len(configured_secret) < 32 or configured_secret.lower() in {
            "change-me-in-production",
            "change-me",
            "secret",
            "changeme",
        }:
            raise RuntimeError(
                "Set a non-placeholder SECRET_KEY with at least 32 characters "
                "when FLASK_ENV=production."
            )

    db.init_app(app)
    csrf.init_app(app)
    _ensure_seed_data(app)

    @app.before_request
    def enforce_user_and_role():
        endpoint = request.endpoint or ""
        if endpoint == "auth.login" or endpoint == "static" or not session.get("user_id"):
            return None

        user = db.session.get(User, session["user_id"])
        if user is None or not user.is_active:
            session.clear()
            if request.is_json:
                return jsonify({"message": "Phiên đăng nhập không còn hợp lệ."}), 401
            return redirect(url_for("auth.login"))

        if endpoint in {
            "auth.users",
            "auth.settings",
            "auth.toggle_user_active",
        } and not user.is_admin:
            abort(403)

        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            if endpoint == "ai.report" and user.role not in {"admin", "manager"}:
                abort(403)
            if endpoint == "disposal.approve_disposal":
                if user.is_admin:
                    return None
                abort(403)
            if endpoint in {"auth.change_password", "auth.logout"} or endpoint in {
                "ai.chat",
                "ai.report",
            }:
                return None
            if endpoint.startswith("inventory.") and user.role in {
                "admin",
                "manager",
                "inspector",
            }:
                return None
            if user.role not in {"admin", "manager"}:
                abort(403)
        return None

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        if request.is_json:
            return jsonify({"message": "Yêu cầu hết hạn hoặc thiếu mã bảo vệ CSRF."}), 400
        return "Yêu cầu không hợp lệ hoặc đã hết hạn. Vui lòng tải lại trang.", 400

    @app.context_processor
    def inject_user():
        user = None
        user_id = session.get("user_id")
        if user_id:
            user = db.session.get(User, user_id)
        return {
            "current_user": user,
            "is_admin_user": bool(user and user.is_admin),
            "can_manage_records": bool(
                user and user.role in {"admin", "manager"}
            ),
            "can_record_inventory": bool(
                user and user.role in {"admin", "manager", "inspector"}
            ),
            "user_display_name": user.full_name if user and user.full_name else (user.username if user else "Khách"),
            "user_role_label": user.display_role if user else "Khách",
        }

    from app.routes import register_routes

    register_routes(app)

    return app
