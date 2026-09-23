"""Dashboard routes."""

from flask import Blueprint, render_template

from app.models import Asset, Department, db
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

    department_rows = (
        db.session.query(Department.name, db.func.count(Asset.id).label("count"), db.func.coalesce(db.func.sum(Asset.value), 0).label("value"))
        .outerjoin(Asset, Asset.department_id == Department.id)
        .group_by(Department.id, Department.name)
        .order_by(db.func.count(Asset.id).desc())
        .all()
    )

    recent_assets = Asset.query.order_by(Asset.id.desc()).limit(5).all()
    summary = {
        "total_assets": total_assets,
        "active_assets": active_assets,
        "repair_assets": repair_assets,
        "disposal_assets": disposal_assets,
        "total_value": float(total_value),
        "department_rows": [
            {"name": row[0], "count": row[1], "value": float(row[2] or 0)}
            for row in department_rows
        ],
        "recent_assets": [
            {
                "asset_code": asset.asset_code,
                "name": asset.name,
                "status": asset.status,
                "department": asset.department.name if asset.department else "—",
                "value": float(asset.value or 0),
            }
            for asset in recent_assets
        ],
    }
    return render_template("dashboard.html", summary=summary)
