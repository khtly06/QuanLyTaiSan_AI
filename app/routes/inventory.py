"""Inventory campaign and physical-count routes."""

from datetime import UTC, date, datetime

from flask import Blueprint, abort, redirect, render_template, request, url_for

from app.models import (
    Asset,
    Inventory,
    InventoryDetail,
    InventoryObservation,
    db,
)
from app.routes.auth import current_user, login_required

bp = Blueprint("inventory", __name__)

ACTUAL_STATUSES = {
    "active": "Đang sử dụng",
    "repair": "Cần sửa chữa",
    "damaged": "Hư hỏng",
    "missing": "Không tìm thấy",
    "other": "Khác",
}


def _parse_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def _inventory_list_data(error=None):
    return {
        "inventory_rows": Inventory.query.order_by(Inventory.id.desc()).all(),
        "error": error,
    }


@bp.route("/inventory", methods=["GET", "POST"])
@login_required
def list_inventory():
    """Create a campaign with a snapshot and list existing campaigns."""
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        try:
            start_date = _parse_date(request.form.get("start_date"))
            end_date = _parse_date(request.form.get("end_date"))
        except ValueError:
            return render_template(
                "inventory.html",
                **_inventory_list_data("Ngày kiểm kê không đúng định dạng."),
            ), 400

        if not name or start_date is None:
            return render_template(
                "inventory.html",
                **_inventory_list_data("Tên đợt và ngày bắt đầu là bắt buộc."),
            ), 400
        if end_date and end_date < start_date:
            return render_template(
                "inventory.html",
                **_inventory_list_data("Ngày kết thúc không được trước ngày bắt đầu."),
            ), 400

        campaign = Inventory(
            name=name,
            start_date=start_date,
            end_date=end_date,
            status="pending",
            created_by=current_user().full_name or current_user().username,
        )
        campaign.details = [
            InventoryDetail(asset=asset, expected_status=asset.status)
            for asset in Asset.query.filter(Asset.status != "disposal").all()
        ]
        if not campaign.details:
            return render_template(
                "inventory.html",
                **_inventory_list_data(
                    "Không có tài sản đang theo dõi để đưa vào đợt kiểm kê."
                ),
            ), 400

        db.session.add(campaign)
        db.session.commit()
        return redirect(
            url_for("inventory.inventory_detail", inventory_id=campaign.id)
        )

    return render_template("inventory.html", **_inventory_list_data())


@bp.route("/inventory/<int:inventory_id>", methods=["GET", "POST"])
@login_required
def inventory_detail(inventory_id):
    """Record an explicit physical observation for a snapshotted asset."""
    campaign = db.session.get(Inventory, inventory_id)
    if campaign is None:
        abort(404)
    if request.method == "POST":
        if campaign.status != "pending":
            abort(400, description="Đợt kiểm kê đã khóa, không thể sửa kết quả.")
        try:
            detail_id = int(request.form.get("detail_id", ""))
        except (TypeError, ValueError):
            abort(400, description="Chi tiết kiểm kê không hợp lệ.")

        detail = db.session.get(InventoryDetail, detail_id)
        if detail is None or detail.inventory_id != campaign.id:
            abort(404)

        actual_status = request.form.get("actual_status", "")
        if actual_status not in ACTUAL_STATUSES:
            abort(400, description="Tình trạng thực tế không hợp lệ.")

        detail.actual_status = actual_status
        detail.variance_note = (request.form.get("variance_note") or "").strip() or None
        user = current_user()
        detail.checked_by = user.full_name or user.username
        detail.checked_at = datetime.now(UTC).replace(tzinfo=None)
        db.session.commit()
        return redirect(
            url_for("inventory.inventory_detail", inventory_id=campaign.id)
        )

    return render_template(
        "inventory_detail.html",
        campaign=campaign,
        actual_statuses=ACTUAL_STATUSES,
        checked_count=sum(detail.actual_status is not None for detail in campaign.details),
        missing_count=sum(
            detail.actual_status == "missing" for detail in campaign.details
        ),
    )


@bp.route("/inventory/<int:inventory_id>/observations", methods=["POST"])
@login_required
def add_observation(inventory_id):
    """Record an item physically found but absent from the asset snapshot."""
    campaign = db.session.get(Inventory, inventory_id)
    if campaign is None:
        abort(404)
    if campaign.status != "pending":
        abort(400, description="Đợt kiểm kê đã khóa, không thể thêm ghi nhận.")

    code = (request.form.get("observed_code") or "").strip()
    name = (request.form.get("observed_name") or "").strip()
    status = request.form.get("actual_status", "")
    if not code or not name or status not in ACTUAL_STATUSES:
        abort(400, description="Mã, tên tài sản và tình trạng thực tế là bắt buộc.")

    user = current_user()
    db.session.add(
        InventoryObservation(
            inventory_id=campaign.id,
            observed_code=code,
            observed_name=name,
            actual_status=status,
            note=(request.form.get("note") or "").strip() or None,
            checked_by=user.full_name or user.username,
        )
    )
    db.session.commit()
    return redirect(url_for("inventory.inventory_detail", inventory_id=campaign.id))


@bp.route("/inventory/<int:inventory_id>/complete", methods=["POST"])
@login_required
def complete_inventory(inventory_id):
    """Lock a campaign only after every expected asset was explicitly counted."""
    campaign = db.session.get(Inventory, inventory_id)
    if campaign is None:
        abort(404)
    if campaign.status != "pending":
        abort(400, description="Đợt kiểm kê không ở trạng thái chờ hoàn thành.")
    if not campaign.details or any(
        detail.actual_status is None for detail in campaign.details
    ):
        abort(400, description="Cần ghi nhận thực tế cho mọi tài sản trước khi hoàn tất.")

    campaign.status = "completed"
    if campaign.end_date is None:
        campaign.end_date = date.today()
    db.session.commit()
    return redirect(url_for("inventory.inventory_detail", inventory_id=campaign.id))
