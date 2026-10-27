"""Routes package registration."""

import logging

from flask import jsonify, redirect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from app.routes.ai import bp as ai_bp
from app.routes.assets import bp as assets_bp
from app.routes.auth import bp as auth_bp
from app.routes.categories import bp as categories_bp
from app.routes.dashboard import bp as dashboard_bp
from app.routes.departments import bp as departments_bp
from app.routes.disposal import bp as disposal_bp
from app.routes.inventory import bp as inventory_bp
from app.routes.repair import bp as repair_bp
from app.routes.reports import bp as reports_bp
from app.routes.transfer import bp as transfer_bp
from app.models import db

logger = logging.getLogger(__name__)


def register_routes(app):
    """Register all application routes."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(assets_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(departments_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(transfer_bp)
    app.register_blueprint(repair_bp)
    app.register_blueprint(disposal_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(ai_bp)

    @app.route("/")
    def index():
        return redirect("/dashboard")

    @app.route("/health")
    def health():
        try:
            db.session.execute(text("SELECT 1"))
        except SQLAlchemyError:
            logger.exception("Application health check failed to query the database.")
            return jsonify({"status": "unavailable"}), 503
        return jsonify({"status": "ok"})
