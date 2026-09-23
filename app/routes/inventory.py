"""Inventory routes."""

from datetime import datetime

from flask import Blueprint, redirect, render_template, request, url_for

from app.models import Inventory, db
from app.routes.auth import login_required

bp = Blueprint("inventory", __name__)


def _parse_date(value):
    """Convert YYYY-MM-DD form value to Python date."""
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


@bp.route("/inventory", methods=["GET", "POST"])
@login_required
def list_inventory():
    """Render inventory rounds with live summary from database."""

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        start_date_str = request.form.get("start_date")
        end_date_str = request.form.get("end_date")

        if not name or not start_date_str:
            return render_template(
                "inventory.html",
                inventory_rows=Inventory.query.order_by(
                    Inventory.id.desc()
                ).all(),
                error="Tên đợt kiểm kê và ngày bắt đầu là bắt buộc.",
            ), 400

        try:
            start_date = _parse_date(start_date_str)
            end_date = _parse_date(end_date_str)
        except ValueError:
            return render_template(
                "inventory.html",
                inventory_rows=Inventory.query.order_by(
                    Inventory.id.desc()
                ).all(),
                error="Ngày kiểm kê không đúng định dạng.",
            ), 400

        inventory = Inventory(
            name=name,
            start_date=start_date,
            end_date=end_date,
            status=request.form.get("status") or "pending",
        )

        db.session.add(inventory)
        db.session.commit()

        return redirect(url_for("inventory.list_inventory"))

    inventory_rows = Inventory.query.order_by(
        Inventory.id.desc()
    ).all()

    return render_template(
        "inventory.html",
        inventory_rows=inventory_rows,
        error=None,
    )