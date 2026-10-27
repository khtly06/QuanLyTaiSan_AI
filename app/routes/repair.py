"""Repair request and lifecycle routes."""

from datetime import datetime

from flask import Blueprint, abort, redirect, render_template, request, url_for

from app.models import Asset, Repair, db
from app.routes.auth import current_user, login_required

bp = Blueprint("repair", __name__)

REPAIR_STATUSES = {
    "pending": "Chờ xử lý",
    "in_progress": "Đang sửa chữa",
    "completed": "Hoàn thành",
    "cancelled": "Đã hủy",
}
OPEN_STATUSES = {"pending", "in_progress"}


def _parse_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def _repair_form_data(error=None):
    return {
        "repairs": Repair.query.order_by(Repair.id.desc()).all(),
        "assets": Asset.query.filter(Asset.status != "disposal")
        .order_by(Asset.name)
        .all(),
        "repair_statuses": REPAIR_STATUSES,
        "error": error,
    }


def _refresh_asset_status(asset):
    if asset.status == "disposal":
        return
    open_request = Repair.query.filter(
        Repair.asset_id == asset.id, Repair.status.in_(OPEN_STATUSES)
    ).first()
    asset.status = "repair" if open_request else "active"


@bp.route("/repairs", methods=["GET", "POST"])
@login_required
def list_repairs():
    """Create a repair request and show repair history."""
    if request.method == "POST":
        description = (request.form.get("description") or "").strip()
        try:
            asset_id = int(request.form.get("asset_id", ""))
            request_date = _parse_date(request.form.get("request_date"))
            cost = float(request.form.get("cost") or 0)
        except (TypeError, ValueError):
            return render_template(
                "repair.html",
                **_repair_form_data("Tài sản, ngày yêu cầu hoặc chi phí không hợp lệ."),
            ), 400

        asset = db.session.get(Asset, asset_id)
        if not description or request_date is None:
            return render_template(
                "repair.html",
                **_repair_form_data(
                    "Vui lòng chọn tài sản, ngày yêu cầu và mô tả sự cố."
                ),
            ), 400
        if asset is None or asset.status == "disposal":
            return render_template(
                "repair.html",
                **_repair_form_data(
                    "Tài sản không tồn tại hoặc đã thanh lý."
                ),
            ), 400
        if cost < 0:
            return render_template(
                "repair.html",
                **_repair_form_data("Chi phí không được âm."),
            ), 400
        if Repair.query.filter(
            Repair.asset_id == asset.id, Repair.status.in_(OPEN_STATUSES)
        ).first():
            return render_template(
                "repair.html",
                **_repair_form_data("Tài sản đã có yêu cầu sửa chữa chưa hoàn tất."),
            ), 400

        user = current_user()
        repair = Repair(
            asset=asset,
            request_date=request_date,
            status="pending",
            description=description,
            cost=cost,
            notes=(request.form.get("notes") or "").strip() or None,
            requested_by=user.full_name or user.username,
            updated_by=user.full_name or user.username,
        )
        asset.status = "repair"
        db.session.add(repair)
        db.session.commit()
        return redirect(url_for("repair.list_repairs"))

    return render_template("repair.html", **_repair_form_data())


@bp.route("/repairs/<int:repair_id>/update", methods=["POST"])
@login_required
def update_repair(repair_id):
    repair = db.session.get(Repair, repair_id)
    if repair is None:
        abort(404)
    if repair.status not in OPEN_STATUSES:
        abort(400, description="Phiếu đã kết thúc và không thể cập nhật.")

    new_status = request.form.get("status", "")
    try:
        cost = float(request.form.get("cost") or 0)
        repair_date = _parse_date(request.form.get("repair_date"))
    except (TypeError, ValueError):
        return render_template(
            "repair.html",
            **_repair_form_data("Ngày sửa chữa hoặc chi phí không hợp lệ."),
        ), 400

    if new_status not in REPAIR_STATUSES or cost < 0:
        return render_template(
            "repair.html",
            **_repair_form_data("Trạng thái hoặc chi phí sửa chữa không hợp lệ."),
        ), 400
    if new_status == "completed" and repair_date is None:
        return render_template(
            "repair.html",
            **_repair_form_data("Cần nhập ngày hoàn thành khi đóng phiếu sửa chữa."),
        ), 400
    if repair.status == "in_progress" and new_status == "pending":
        abort(400, description="Không thể chuyển phiếu đang xử lý về trạng thái chờ.")

    repair.status = new_status
    repair.cost = cost
    repair.repair_date = repair_date
    user = current_user()
    repair.updated_by = user.full_name or user.username
    _refresh_asset_status(repair.asset)
    db.session.commit()
    return redirect(url_for("repair.list_repairs"))
