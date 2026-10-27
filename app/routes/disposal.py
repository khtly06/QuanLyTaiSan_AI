"""Disposal request and approval routes."""

from datetime import UTC, datetime

from flask import Blueprint, abort, redirect, render_template, request, url_for

from app.models import Asset, Disposal, Repair, db
from app.routes.auth import current_user, login_required

bp = Blueprint("disposal", __name__)
FINAL_DISPOSAL_STATUSES = {"approved", "rejected"}
OPEN_REPAIR_STATUSES = {"pending", "in_progress"}


def _disposal_form_data(error=None):
    return {
        "disposals": Disposal.query.order_by(Disposal.id.desc()).all(),
        "assets": Asset.query.filter(Asset.status != "disposal")
        .order_by(Asset.name)
        .all(),
        "error": error,
    }


@bp.route("/disposals", methods=["GET", "POST"])
@login_required
def list_disposals():
    """Create a disposal request; approval is a separate administrator action."""
    if request.method == "POST":
        reason = (request.form.get("reason") or "").strip()
        try:
            asset_id = int(request.form.get("asset_id", ""))
            disposal_date = datetime.strptime(
                request.form.get("disposal_date", ""), "%Y-%m-%d"
            ).date()
            liquidation_value = float(request.form.get("liquidation_value") or 0)
        except (TypeError, ValueError):
            return render_template(
                "disposal.html",
                **_disposal_form_data(
                    "Tài sản, ngày thanh lý hoặc giá trị không hợp lệ."
                ),
            ), 400

        asset = db.session.get(Asset, asset_id)
        if not reason or asset is None or asset.status != "active":
            return render_template(
                "disposal.html",
                **_disposal_form_data(
                    "Cần chọn tài sản đang sử dụng và nhập lý do thanh lý."
                ),
            ), 400
        if liquidation_value < 0:
            return render_template(
                "disposal.html",
                **_disposal_form_data("Giá trị thanh lý không được âm."),
            ), 400
        if Repair.query.filter(
            Repair.asset_id == asset.id,
            Repair.status.in_(OPEN_REPAIR_STATUSES),
        ).first():
            return render_template(
                "disposal.html",
                **_disposal_form_data(
                    "Không thể đề nghị thanh lý khi tài sản còn phiếu sửa chữa mở."
                ),
            ), 400
        if Disposal.query.filter(
            Disposal.asset_id == asset.id,
            Disposal.status.in_({"requested", "approved"}),
        ).first():
            return render_template(
                "disposal.html",
                **_disposal_form_data(
                    "Tài sản đã có hồ sơ thanh lý đang xử lý hoặc đã được duyệt."
                ),
            ), 400

        user = current_user()
        db.session.add(
            Disposal(
                asset=asset,
                disposal_date=disposal_date,
                reason=reason,
                liquidation_value=liquidation_value,
                status="requested",
                requested_by=user.full_name or user.username,
            )
        )
        db.session.commit()
        return redirect(url_for("disposal.list_disposals"))

    return render_template("disposal.html", **_disposal_form_data())


@bp.route("/disposals/<int:disposal_id>/decision", methods=["POST"])
@login_required
def approve_disposal(disposal_id):
    """Approve or reject a pending request; route is restricted to administrators."""
    disposal = db.session.get(Disposal, disposal_id)
    if disposal is None:
        abort(404)
    if disposal.status != "requested":
        abort(400, description="Hồ sơ thanh lý không còn chờ phê duyệt.")

    decision = request.form.get("decision")
    if decision not in FINAL_DISPOSAL_STATUSES:
        abort(400, description="Quyết định thanh lý không hợp lệ.")

    asset = disposal.asset
    if decision == "approved":
        if asset.status != "active":
            abort(400, description="Chỉ tài sản đang sử dụng mới được duyệt thanh lý.")
        if Repair.query.filter(
            Repair.asset_id == asset.id,
            Repair.status.in_(OPEN_REPAIR_STATUSES),
        ).first():
            abort(400, description="Tài sản còn phiếu sửa chữa mở.")
        asset.status = "disposal"

    user = current_user()
    disposal.status = decision
    disposal.decided_by = user.full_name or user.username
    disposal.decided_at = datetime.now(UTC).replace(tzinfo=None)
    db.session.commit()
    return redirect(url_for("disposal.list_disposals"))
