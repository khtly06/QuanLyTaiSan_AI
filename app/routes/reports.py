"""Reports routes."""

from flask import Blueprint, render_template

from app.models import (
    Asset,
    Category,
    Department,
    Disposal,
    Inventory,
    Repair,
    Transfer,
    db,
)
from app.routes.auth import login_required
from app.routes.repair import REPAIR_STATUSES

bp = Blueprint("reports", __name__)
DISPOSAL_STATUS_LABELS = {
    "requested": "Chờ duyệt",
    "approved": "Đã duyệt",
    "rejected": "Từ chối",
}
INVENTORY_STATUS_LABELS = {
    "pending": "Đang thực hiện",
    "completed": "Hoàn thành",
}


@bp.route("/reports")
@login_required
def reports():
    """Render a report dashboard from live database data."""

    # Tổng quan tài sản
    total_assets = Asset.query.count()

    active_assets = Asset.query.filter_by(status="active").count()

    repair_assets = Asset.query.filter_by(status="repair").count()

    disposed_assets = Asset.query.filter_by(status="disposal").count()

    total_value = (
        db.session.query(
            db.func.coalesce(db.func.sum(Asset.value), 0)
        ).scalar()
        or 0
    )

    # Thống kê tài sản theo phòng ban
    department_rows = (
        db.session.query(
            Department.name,
            db.func.count(Asset.id).label("count"),
        )
        .outerjoin(
            Asset,
            Asset.department_id == Department.id,
        )
        .group_by(
            Department.id,
            Department.name,
        )
        .order_by(
            db.func.count(Asset.id).desc()
        )
        .all()
    )

    # Thống kê tài sản theo loại
    category_rows = (
        db.session.query(
            Category.name,
            db.func.count(Asset.id).label("count"),
            db.func.coalesce(
                db.func.sum(Asset.value),
                0,
            ).label("total_value"),
        )
        .outerjoin(
            Asset,
            Asset.category_id == Category.id,
        )
        .group_by(
            Category.id,
            Category.name,
        )
        .order_by(
            db.func.count(Asset.id).desc()
        )
        .all()
    )

    # Sửa chữa
    repair_rows = (
        Repair.query
        .order_by(Repair.id.desc())
        .all()
    )

    total_repairs = Repair.query.count()

    pending_repairs = Repair.query.filter_by(
        status="pending"
    ).count()

    in_progress_repairs = Repair.query.filter_by(
        status="in_progress"
    ).count()

    completed_repairs = Repair.query.filter_by(
        status="completed"
    ).count()

    repair_cost = (
        db.session.query(
            db.func.coalesce(
                db.func.sum(Repair.cost),
                0,
            )
        ).scalar()
        or 0
    )

    # Điều chuyển
    total_transfers = Transfer.query.count()

    transfer_rows = (
        Transfer.query
        .order_by(Transfer.id.desc())
        .limit(10)
        .all()
    )

    # Thanh lý
    total_disposals = Disposal.query.count()

    disposal_rows = (
        Disposal.query
        .order_by(Disposal.id.desc())
        .limit(10)
        .all()
    )

    # Kiểm kê
    total_inventory = Inventory.query.count()

    inventory_rows = (
        Inventory.query
        .order_by(Inventory.id.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "reports.html",
        total_assets=total_assets,
        active_assets=active_assets,
        repair_assets=repair_assets,
        disposed_assets=disposed_assets,
        total_value=float(total_value),

        department_rows=department_rows,
        category_rows=category_rows,

        repair_rows=repair_rows,
        total_repairs=total_repairs,
        pending_repairs=pending_repairs,
        in_progress_repairs=in_progress_repairs,
        completed_repairs=completed_repairs,
        repair_status_labels=REPAIR_STATUSES,
        repair_cost=float(repair_cost),

        total_transfers=total_transfers,
        transfer_rows=transfer_rows,

        total_disposals=total_disposals,
        disposal_rows=disposal_rows,
        disposal_status_labels=DISPOSAL_STATUS_LABELS,

        total_inventory=total_inventory,
        inventory_rows=inventory_rows,
        inventory_status_labels=INVENTORY_STATUS_LABELS,
    )