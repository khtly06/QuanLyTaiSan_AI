"""Department routes."""

from flask import Blueprint, abort, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError

from app.models import Asset, Department, Transfer, db
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
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return render_template(
                "departments.html",
                departments=Department.query.order_by(Department.name).all(),
                error="Tên hoặc mã phòng ban đã tồn tại.",
            ), 400
        return redirect(url_for("departments.list_departments"))
    return render_template("departments.html", departments=Department.query.order_by(Department.name).all(), error=None)


@bp.route("/departments/<int:department_id>/edit", methods=["POST"])
@login_required
def update_department(department_id):
    department = db.session.get(Department, department_id)
    if department is None:
        abort(404)
    name = (request.form.get("name") or "").strip()
    code = (request.form.get("code") or "").strip()
    if not name or not code:
        return render_template(
            "departments.html",
            departments=Department.query.order_by(Department.name).all(),
            error="Tên và mã phòng ban không được để trống.",
        ), 400
    department.name = name
    department.code = code
    department.description = (request.form.get("description") or "").strip() or None
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return render_template(
            "departments.html",
            departments=Department.query.order_by(Department.name).all(),
            error="Tên hoặc mã phòng ban đã được sử dụng.",
        ), 400
    return redirect(url_for("departments.list_departments"))


@bp.route("/departments/<int:department_id>/delete", methods=["POST"])
@login_required
def delete_department(department_id):
    department = db.session.get(Department, department_id)
    if department is None:
        abort(404)
    if (
        Asset.query.filter_by(department_id=department.id).first()
        or Transfer.query.filter(
            (Transfer.from_department_id == department.id)
            | (Transfer.to_department_id == department.id)
        ).first()
    ):
        return render_template(
            "departments.html",
            departments=Department.query.order_by(Department.name).all(),
            error="Không thể xóa phòng ban đang được tài sản hoặc lịch sử sử dụng.",
        ), 400
    db.session.delete(department)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return render_template(
            "departments.html",
            departments=Department.query.order_by(Department.name).all(),
            error="Không thể xóa phòng ban đang được tài sản hoặc lịch sử sử dụng.",
        ), 400
    return redirect(url_for("departments.list_departments"))
