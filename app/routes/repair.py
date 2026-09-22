"""Repair routes."""

from flask import Blueprint, redirect, render_template, request, url_for

from app.models import Asset, Repair, db
from app.routes.auth import login_required

bp = Blueprint("repair", __name__)


@bp.route("/repairs", methods=["GET", "POST"])
@login_required
def list_repairs():
    """Render repair requests using real data."""
    if request.method == "POST":
        asset_id = request.form.get("asset_id")
        description = (request.form.get("description") or "").strip()
        if not asset_id or not description:
            return render_template("repair.html", repairs=Repair.query.order_by(Repair.id.desc()).all(), error="Vui lòng chọn tài sản và mô tả nhu cầu sửa chữa."), 400
        repair = Repair(
            asset_id=int(asset_id),
            request_date=request.form.get("request_date") or None,
            status=request.form.get("status") or "pending",
            description=description,
            cost=float(request.form.get("cost") or 0),
        )
        db.session.add(repair)
        db.session.commit()
        return redirect(url_for("repair.list_repairs"))

    repairs = Repair.query.order_by(Repair.id.desc()).all()
    return render_template("repair.html", repairs=repairs, assets=Asset.query.order_by(Asset.name).all(), error=None)
