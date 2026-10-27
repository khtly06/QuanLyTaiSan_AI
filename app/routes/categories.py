"""Category routes."""

from flask import Blueprint, abort, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError

from app.models import Asset, Category, db
from app.routes.auth import login_required

bp = Blueprint("categories", __name__)


@bp.route("/categories", methods=["GET", "POST"])
@login_required
def list_categories():
    """Render category page backed by the real database."""
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        description = (request.form.get("description") or "").strip()
        if not name:
            return render_template("categories.html", categories=Category.query.order_by(Category.name).all(), error="Tên danh mục không được để trống."), 400
        category = Category(name=name, description=description or None)
        db.session.add(category)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return render_template(
                "categories.html",
                categories=Category.query.order_by(Category.name).all(),
                error="Tên danh mục đã tồn tại hoặc đang được tài liệu tham chiếu.",
            ), 400
        return redirect(url_for("categories.list_categories"))
    return render_template("categories.html", categories=Category.query.order_by(Category.name).all(), error=None)


@bp.route("/categories/<int:category_id>/edit", methods=["POST"])
@login_required
def update_category(category_id):
    category = db.session.get(Category, category_id)
    if category is None:
        abort(404)
    name = (request.form.get("name") or "").strip()
    if not name:
        return render_template(
            "categories.html",
            categories=Category.query.order_by(Category.name).all(),
            error="Tên danh mục không được để trống.",
        ), 400
    category.name = name
    category.description = (request.form.get("description") or "").strip() or None
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return render_template(
            "categories.html",
            categories=Category.query.order_by(Category.name).all(),
            error="Tên danh mục đã được sử dụng.",
        ), 400
    return redirect(url_for("categories.list_categories"))


@bp.route("/categories/<int:category_id>/delete", methods=["POST"])
@login_required
def delete_category(category_id):
    category = db.session.get(Category, category_id)
    if category is None:
        abort(404)
    if Asset.query.filter_by(category_id=category.id).first():
        return render_template(
            "categories.html",
            categories=Category.query.order_by(Category.name).all(),
            error="Không thể xóa danh mục đang được tài sản sử dụng.",
        ), 400
    db.session.delete(category)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return render_template(
            "categories.html",
            categories=Category.query.order_by(Category.name).all(),
            error="Không thể xóa danh mục đang được tài sản sử dụng.",
        ), 400
    return redirect(url_for("categories.list_categories"))
