"""Asset routes."""

from flask import Blueprint, redirect, render_template, request, url_for

from app.models import Asset, Category, Department, db
from app.routes.auth import login_required

bp = Blueprint("assets", __name__)


@bp.route("/assets", methods=["GET", "POST"])
@login_required
def list_assets():
    """List assets with search, filter, and create form support."""
    if request.method == "POST":
        asset_code = (request.form.get("asset_code") or "").strip()
        name = (request.form.get("name") or "").strip()
        category_id = request.form.get("category_id")
        department_id = request.form.get("department_id")
        if not asset_code or not name or not category_id or not department_id:
            return render_template(
                "assets.html",
                assets=Asset.query.order_by(Asset.id.desc()).all(),
                categories=Category.query.order_by(Category.name).all(),
                departments=Department.query.order_by(Department.name).all(),
                error="Vui lòng nhập mã tài sản, tên, danh mục và phòng ban.",
            ), 400
        asset = Asset(
            asset_code=asset_code,
            name=name,
            category_id=int(category_id),
            department_id=int(department_id),
            user_name=request.form.get("user_name") or None,
            purchase_date=request.form.get("purchase_date") or None,
            value=float(request.form.get("value") or 0),
            status=request.form.get("status") or "active",
            location=request.form.get("location") or None,
            notes=request.form.get("notes") or None,
        )
        db.session.add(asset)
        db.session.commit()
        return redirect(url_for("assets.list_assets"))

    query = request.args.get("q", "").strip()
    category_filter = request.args.get("category_id")
    department_filter = request.args.get("department_id")
    status_filter = request.args.get("status")

    items = Asset.query
    if query:
        items = items.filter(
            (Asset.name.ilike(f"%{query}%")) | (Asset.asset_code.ilike(f"%{query}%"))
        )
    if category_filter:
        items = items.filter_by(category_id=int(category_filter))
    if department_filter:
        items = items.filter_by(department_id=int(department_filter))
    if status_filter:
        items = items.filter_by(status=status_filter)
    items = items.order_by(Asset.id.desc()).all()

    return render_template(
        "assets.html",
        assets=items,
        categories=Category.query.order_by(Category.name).all(),
        departments=Department.query.order_by(Department.name).all(),
        error=None,
    )


@bp.route("/assets/<int:asset_id>")
@login_required
def get_asset(asset_id):
    """Display asset detail page."""
    asset = Asset.query.get_or_404(asset_id)
    return render_template("asset_detail.html", asset=asset)


@bp.route("/assets/<int:asset_id>/delete", methods=["POST"])
@login_required
def delete_asset(asset_id):
    """Delete an asset record."""
    asset = Asset.query.get_or_404(asset_id)
    db.session.delete(asset)
    db.session.commit()
    return redirect(url_for("assets.list_assets"))
