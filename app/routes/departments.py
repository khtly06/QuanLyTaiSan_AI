"""Department routes."""

from flask import Blueprint, redirect, render_template, request, url_for

from app.models import Department, db
from app.routes.auth import login_required

bp = Blueprint("departments", __name__)


@bp.route("/departments", methods=["GET", "POST"])
@login_required
def list_departments():
    """Render department page backed by the real database."""
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        code = (request.form.get("code") or "").strip()
        if not name or not code:
            return render_template("departments.html", departments=Department.query.order_by(Department.name).all(), error="Tên và mã phòng ban không được trống."), 400
        department = Department(name=name, code=code, description=request.form.get("description") or None)
        db.session.add(department)
        db.session.commit()
        return redirect(url_for("departments.list_departments"))
    return render_template("departments.html", departments=Department.query.order_by(Department.name).all(), error=None)
