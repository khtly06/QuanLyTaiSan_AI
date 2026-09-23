"""Disposal routes."""

from datetime import datetime

from flask import Blueprint, redirect, render_template, request, url_for

from app.models import Asset, Disposal, db
from app.routes.auth import login_required

bp = Blueprint("disposal", __name__)


def _parse_date(value):
    """Convert YYYY-MM-DD form value to Python date."""
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def _disposal_form_data():
    """Load data needed by the disposal form."""
    return {
        "disposals": Disposal.query.order_by(
            Disposal.id.desc()
        ).all(),
        "assets": Asset.query.order_by(
            Asset.name
        ).all(),
    }


@bp.route("/disposals", methods=["GET", "POST"])
@login_required
def list_disposals():
    """Render disposal history from the live database."""

    if request.method == "POST":
        asset_id = request.form.get("asset_id")
        reason = (request.form.get("reason") or "").strip()
        disposal_date_str = request.form.get("disposal_date")

        if not asset_id or not reason or not disposal_date_str:
            data = _disposal_form_data()
            data["error"] = (
                "Vui lòng chọn tài sản, ngày thanh lý "
                "và lý do thanh lý."
            )
            return render_template("disposal.html", **data), 400

        try:
            disposal_date = _parse_date(disposal_date_str)
        except ValueError:
            data = _disposal_form_data()
            data["error"] = "Ngày thanh lý không đúng định dạng."
            return render_template("disposal.html", **data), 400

        try:
            liquidation_value = float(
                request.form.get("liquidation_value") or 0
            )
        except (TypeError, ValueError):
            data = _disposal_form_data()
            data["error"] = "Giá trị thanh lý không hợp lệ."
            return render_template("disposal.html", **data), 400

        if liquidation_value < 0:
            data = _disposal_form_data()
            data["error"] = "Giá trị thanh lý không được âm."
            return render_template("disposal.html", **data), 400

        disposal = Disposal(
            asset_id=int(asset_id),
            disposal_date=disposal_date,
            reason=reason,
            liquidation_value=liquidation_value,
            status=request.form.get("status") or "requested",
        )

        db.session.add(disposal)
        db.session.commit()

        return redirect(url_for("disposal.list_disposals"))

    data = _disposal_form_data()
    data["error"] = None

    return render_template("disposal.html", **data)