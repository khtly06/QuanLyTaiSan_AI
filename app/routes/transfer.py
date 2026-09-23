"""Transfer routes."""

from datetime import datetime

from flask import Blueprint, redirect, render_template, request, url_for

from app.models import Asset, Department, Transfer, db
from app.routes.auth import login_required

bp = Blueprint("transfer", __name__)


def _parse_date(value):
    """Convert YYYY-MM-DD form value to Python date."""
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


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
                transfers=Transfer.query.order_by(
                    Transfer.id.desc()
                ).all(),
                departments=Department.query.order_by(
                    Department.name
                ).all(),
                assets=Asset.query.order_by(
                    Asset.name
                ).all(),
                error="Vui lòng nhập đầy đủ thông tin điều chuyển.",
            ), 400

        try:
            transfer_date = _parse_date(transfer_date_str)
        except ValueError:
            return render_template(
                "transfer.html",
                transfers=Transfer.query.order_by(
                    Transfer.id.desc()
                ).all(),
                departments=Department.query.order_by(
                    Department.name
                ).all(),
                assets=Asset.query.order_by(
                    Asset.name
                ).all(),
                error="Ngày điều chuyển không đúng định dạng.",
            ), 400

        if int(from_department_id) == int(to_department_id):
            return render_template(
                "transfer.html",
                transfers=Transfer.query.order_by(
                    Transfer.id.desc()
                ).all(),
                departments=Department.query.order_by(
                    Department.name
                ).all(),
                assets=Asset.query.order_by(
                    Asset.name
                ).all(),
                error="Phòng ban chuyển đến phải khác phòng ban hiện tại.",
            ), 400

        transfer = Transfer(
            asset_id=int(asset_id),
            from_department_id=int(from_department_id),
            to_department_id=int(to_department_id),
            transfer_date=transfer_date,
            reason=request.form.get("reason") or None,
            notes=request.form.get("notes") or None,
        )

        db.session.add(transfer)
        db.session.commit()

        return redirect(url_for("transfer.list_transfers"))

    return render_template(
        "transfer.html",
        transfers=Transfer.query.order_by(Transfer.id.desc()).all(),
        departments=Department.query.order_by(Department.name).all(),
        assets=Asset.query.order_by(Asset.name).all(),
        error=None,
    )