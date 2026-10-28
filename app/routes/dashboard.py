"""Dashboard routes."""

from flask import Blueprint, render_template

from app.models import Asset, Department, Disposal, Repair, db
from app.routes.auth import login_required

bp = Blueprint("dashboard", __name__)


@bp.route("/dashboard")
@login_required
def dashboard():
    """Render the dashboard overview using live database data."""
    total_assets = Asset.query.count()
    active_assets = Asset.query.filter_by(status="active").count()
    repair_assets = Asset.query.filter_by(status="repair").count()
    disposal_assets = Asset.query.filter_by(status="disposal").count()
    total_value = db.session.query(db.func.coalesce(db.func.sum(Asset.value), 0)).scalar() or 0
    status_counts = {
        status: count
        for status, count in (
            db.session.query(Asset.status, db.func.count(Asset.id))
            .group_by(Asset.status)
            .all()
        )
    }
    chart_statuses = (
        ("active", "Đang sử dụng"),
        ("repair", "Đang sửa chữa"),
        ("disposal", "Chờ thanh lý"),
    )
    largest_status_count = max(
        (status_counts.get(status, 0) for status, _ in chart_statuses),
        default=0,
    )
    status_rows = [
        {
            "key": status,
            "label": label,
            "count": status_counts.get(status, 0),
            "percentage": round(
                status_counts.get(status, 0) / largest_status_count * 100
            )
            if largest_status_count
            else 0,
        }
        for status, label in chart_statuses
    ]

    department_rows = (
        db.session.query(Department.name, db.func.count(Asset.id).label("count"), db.func.coalesce(db.func.sum(Asset.value), 0).label("value"))
        .outerjoin(Asset, Asset.department_id == Department.id)
        .group_by(Department.id, Department.name)
        .order_by(db.func.count(Asset.id).desc())
        .all()
    )

    recent_assets = Asset.query.order_by(Asset.id.desc()).limit(5).all()
    pending_repairs = Repair.query.filter_by(status="pending").count()
    pending_disposals = Disposal.query.filter_by(status="requested").count()
    summary = {
        "total_assets": total_assets,
        "active_assets": active_assets,
        "repair_assets": repair_assets,
        "disposal_assets": disposal_assets,
        "total_value": float(total_value),
        "status_rows": status_rows,
        "pending_repairs": pending_repairs,
        "pending_disposals": pending_disposals,
        "department_rows": [
            {"name": row[0], "count": row[1], "value": float(row[2] or 0)}
            for row in department_rows
        ],
        "recent_assets": [
            {
                "asset_code": asset.asset_code,
                "name": asset.name,
                "status": asset.status,
                "location": asset.location or "—",
                "status_label": {
                    "active": "Đang sử dụng",
                    "repair": "Đang sửa chữa",
                    "disposal": "Chờ thanh lý",
                }.get(asset.status, asset.status),
                "value": float(asset.value or 0),
            }
            for asset in recent_assets
        ],
    }
    return render_template("dashboard.html", summary=summary)
