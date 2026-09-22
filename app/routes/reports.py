"""Reports routes."""

from flask import Blueprint, render_template

from app.models import Asset, Department, Repair, db
from app.routes.auth import login_required

bp = Blueprint("reports", __name__)


@bp.route("/reports")
@login_required
def reports():
    """Render a report dashboard from live asset and department data."""
    total_assets = Asset.query.count()
    active_assets = Asset.query.filter_by(status="active").count()
    repair_assets = Asset.query.filter_by(status="repair").count()
    total_value = db.session.query(db.func.coalesce(db.func.sum(Asset.value), 0)).scalar() or 0

    department_rows = (
        db.session.query(Department.name, db.func.count(Asset.id).label("count"))
        .outerjoin(Asset, Asset.department_id == Department.id)
        .group_by(Department.id, Department.name)
        .order_by(db.func.count(Asset.id).desc())
        .all()
    )
    repair_rows = Repair.query.order_by(Repair.id.desc()).all()
    return render_template(
        "reports.html",
        total_assets=total_assets,
        active_assets=active_assets,
        repair_assets=repair_assets,
        total_value=float(total_value),
        department_rows=department_rows,
        repair_rows=repair_rows,
    )
