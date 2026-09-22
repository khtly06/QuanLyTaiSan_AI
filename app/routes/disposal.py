"""Disposal routes."""

from flask import Blueprint, redirect, render_template, request, url_for

from app.models import Asset, Disposal, db
from app.routes.auth import login_required

bp = Blueprint("disposal", __name__)


@bp.route("/disposals", methods=["GET", "POST"])
@login_required
def list_disposals():
    """Render disposal history from the live database."""
    if request.method == "POST":
        asset_id = request.form.get("asset_id")
        reason = (request.form.get("reason") or "").strip()
        if not asset_id or not reason:
            return render_template("disposal.html", disposals=Disposal.query.order_by(Disposal.id.desc()).all(), assets=Asset.query.order_by(Asset.name).all(), error="Vui lòng chọn tài sản và lý do thanh lý."), 400
        disposal = Disposal(
            asset_id=int(asset_id),
            disposal_date=request.form.get("disposal_date") or None,
            reason=reason,
            liquidation_value=float(request.form.get("liquidation_value") or 0),
            status=request.form.get("status") or "requested",
        )
        db.session.add(disposal)
        db.session.commit()
        return redirect(url_for("disposal.list_disposals"))

    return render_template("disposal.html", disposals=Disposal.query.order_by(Disposal.id.desc()).all(), assets=Asset.query.order_by(Asset.name).all(), error=None)
