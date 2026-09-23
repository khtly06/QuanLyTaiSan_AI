"""Repair routes."""

from datetime import datetime

from flask import Blueprint, redirect, render_template, request, url_for

from app.models import Asset, Repair, db
from app.routes.auth import login_required

bp = Blueprint("repair", __name__)


def _parse_date(value):
    """Convert YYYY-MM-DD form value to Python date."""
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def _repair_form_data():
    """Load data needed by the repair form."""
    return {
        "repairs": Repair.query.order_by(Repair.id.desc()).all(),
        "assets": Asset.query.order_by(Asset.name).all(),
    }


@bp.route("/repairs", methods=["GET", "POST"])
@login_required
def list_repairs():
    """Render repair requests using real data."""

    if request.method == "POST":
        asset_id = request.form.get("asset_id")
        description = (request.form.get("description") or "").strip()
        request_date_str = request.form.get("request_date")
        repair_date_str = request.form.get("repair_date")

        if not asset_id or not description or not request_date_str:
            data = _repair_form_data()
            data["error"] = (
                "Vui lòng chọn tài sản, ngày yêu cầu "
                "và mô tả nhu cầu sửa chữa."
            )
            return render_template("repair.html", **data), 400

        try:
            request_date = _parse_date(request_date_str)
            repair_date = _parse_date(repair_date_str)
        except ValueError:
            data = _repair_form_data()
            data["error"] = "Ngày sửa chữa không đúng định dạng."
            return render_template("repair.html", **data), 400

        try:
            cost = float(request.form.get("cost") or 0)
        except (TypeError, ValueError):
            data = _repair_form_data()
            data["error"] = "Chi phí sửa chữa không hợp lệ."
            return render_template("repair.html", **data), 400

        if cost < 0:
            data = _repair_form_data()
            data["error"] = "Chi phí sửa chữa không được âm."
            return render_template("repair.html", **data), 400

        repair = Repair(
            asset_id=int(asset_id),
            request_date=request_date,
            repair_date=repair_date,
            status=request.form.get("status") or "pending",
            description=description,
            cost=cost,
            notes=(request.form.get("notes") or "").strip() or None,
        )

        db.session.add(repair)
        db.session.commit()

        return redirect(url_for("repair.list_repairs"))

    data = _repair_form_data()
    data["error"] = None

    return render_template("repair.html", **data)