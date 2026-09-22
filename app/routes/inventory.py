"""Inventory routes."""

from flask import Blueprint, redirect, render_template, request, url_for

from app.models import Inventory, db
from app.routes.auth import login_required

bp = Blueprint("inventory", __name__)


@bp.route("/inventory", methods=["GET", "POST"])
@login_required
def list_inventory():
    """Render inventory rounds with live summary from database."""
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        start_date = request.form.get("start_date")
        if not name or not start_date:
            return render_template("inventory.html", inventory_rows=Inventory.query.order_by(Inventory.id.desc()).all(), error="Tên đợt kiểm kê và ngày bắt đầu là bắt buộc."), 400
        inventory = Inventory(name=name, start_date=start_date, end_date=request.form.get("end_date") or None, status=request.form.get("status") or "pending")
        db.session.add(inventory)
        db.session.commit()
        return redirect(url_for("inventory.list_inventory"))

    inventory_rows = Inventory.query.order_by(Inventory.id.desc()).all()
    return render_template("inventory.html", inventory_rows=inventory_rows, error=None)
