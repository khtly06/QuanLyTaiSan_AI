"""Category routes."""

from flask import Blueprint, redirect, render_template, request, url_for

from app.models import Category, db
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
        db.session.commit()
        return redirect(url_for("categories.list_categories"))
    return render_template("categories.html", categories=Category.query.order_by(Category.name).all(), error=None)
