"""Transfer routes."""

from datetime import datetime

from flask import Blueprint, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError

from app.models import Asset, Department, Disposal, Transfer, db
from app.routes.auth import current_user, login_required

bp = Blueprint("transfer", __name__)


def _parse_date(value):
    """Convert YYYY-MM-DD form value to Python date."""
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def _transfer_form_data(error=None):
    """Load data needed to render the transfer form and any validation error."""
    return {
        "transfers": Transfer.query.order_by(Transfer.id.desc()).all(),
        "departments": Department.query.order_by(Department.name).all(),
        "assets": Asset.query.order_by(Asset.name).all(),
        "error": error,
    }


@bp.route("/transfers", methods=["GET", "POST"])
@login_required
def list_transfers():
    """Render transfer history using the real database."""

    if request.method == "POST":
        asset_id = request.form.get("asset_id")
        from_department_id = request.form.get("from_department_id")
        to_department_id = request.form.get("to_department_id")
        transfer_date_str = request.form.get("transfer_date")

        if (
            not asset_id
            or not from_department_id
            or not to_department_id
            or not transfer_date_str
        ):
            return render_template(
                "transfer.html",
                **_transfer_form_data("Vui lòng nhập đầy đủ thông tin điều chuyển."),
            ), 400

        try:
            asset_id = int(asset_id)
            from_department_id = int(from_department_id)
            to_department_id = int(to_department_id)
            transfer_date = _parse_date(transfer_date_str)
        except (TypeError, ValueError):
            return render_template(
                "transfer.html",
                **_transfer_form_data("Thông tin điều chuyển hoặc ngày không hợp lệ."),
            ), 400

        asset = db.session.get(Asset, asset_id)
        source = db.session.get(Department, from_department_id)
        destination = db.session.get(Department, to_department_id)
        if asset is None or source is None or destination is None:
            return render_template(
                "transfer.html",
                **_transfer_form_data("Tài sản hoặc phòng ban không tồn tại."),
            ), 400

        if source.id == destination.id:
            return render_template(
                "transfer.html",
                **_transfer_form_data(
                    "Phòng ban chuyển đến phải khác phòng ban hiện tại."
                ),
            ), 400

        if asset.department_id != source.id:
            return render_template(
                "transfer.html",
                **_transfer_form_data(
                    "Phòng ban chuyển đi không khớp với vị trí hiện tại của tài sản."
                ),
            ), 400

        if asset.status != "active":
            return render_template(
                "transfer.html",
                **_transfer_form_data(
                    "Chỉ tài sản đang sử dụng mới được điều chuyển."
                ),
            ), 400
        if Disposal.query.filter_by(asset_id=asset.id, status="requested").first():
            return render_template(
                "transfer.html",
                **_transfer_form_data(
                    "Không thể điều chuyển tài sản đang chờ duyệt thanh lý."
                ),
            ), 400

        transfer = Transfer(
            asset_id=asset.id,
            from_department_id=source.id,
            to_department_id=destination.id,
            transfer_date=transfer_date,
            reason=(request.form.get("reason") or "").strip() or None,
            notes=(request.form.get("notes") or "").strip() or None,
            performed_by=(
                current_user().full_name or current_user().username
            ),
        )

        asset.department_id = destination.id
        db.session.add(transfer)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return render_template(
                "transfer.html",
                **_transfer_form_data("Không thể lưu điều chuyển. Vui lòng kiểm tra dữ liệu."),
            ), 400

        return redirect(url_for("transfer.list_transfers"))

    return render_template("transfer.html", **_transfer_form_data())