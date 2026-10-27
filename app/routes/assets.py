"""Asset routes with live CRUD operations."""

from datetime import datetime
import math

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError

from app.models import Asset, Category, Department, db
from app.routes.auth import login_required

bp = Blueprint("assets", __name__)

STATUS_OPTIONS = (
    ("active", "Đang sử dụng"),
    ("repair", "Đang sửa chữa"),
    ("disposal", "Thanh lý"),
)


def _asset_form_data():
    return {
        "categories": Category.query.order_by(Category.name).all(),
        "departments": Department.query.order_by(Department.name).all(),
        "status_options": STATUS_OPTIONS,
    }


def _validate_asset_form(form, asset=None):
    asset_code = (form.get("asset_code") or "").strip()
    name = (form.get("name") or "").strip()
    category_id = form.get("category_id")
    department_id = form.get("department_id")
    if not asset_code or not name or not category_id or not department_id:
        return "Vui lòng nhập đầy đủ mã, tên, danh mục và phòng ban."

    duplicate = Asset.query.filter(Asset.asset_code == asset_code)
    if asset is not None:
        duplicate = duplicate.filter(Asset.id != asset.id)
    if duplicate.first():
        return f"Mã tài sản '{asset_code}' đã tồn tại."

    try:
        category_id = int(category_id)
        department_id = int(department_id)
        value = float(form.get("value") or 0)
    except (TypeError, ValueError):
        return "Danh mục, phòng ban hoặc giá trị tài sản không hợp lệ."

    if value < 0:
        return "Giá trị tài sản không được âm."
    if not math.isfinite(value):
        return "Giá trị tài sản không hợp lệ."
    purchase_date = form.get("purchase_date")
    if purchase_date:
        try:
            datetime.strptime(purchase_date, "%Y-%m-%d")
        except ValueError:
            return "Ngày mua không hợp lệ."
    if not db.session.get(Category, category_id) or not db.session.get(
        Department, department_id
    ):
        return "Danh mục hoặc phòng ban không tồn tại."

    status = form.get("status") or "active"
    if status not in dict(STATUS_OPTIONS):
        return "Trạng thái tài sản không hợp lệ."
    if asset is None and status != "active":
        return "Tài sản mới phải được tạo ở trạng thái đang sử dụng."
    if asset is not None and status != asset.status:
        return "Chỉ quy trình sửa chữa hoặc thanh lý mới được thay đổi trạng thái tài sản."

    return None


def _apply_form(asset, form):
    asset.asset_code = (form.get("asset_code") or "").strip()
    asset.name = (form.get("name") or "").strip()
    asset.category_id = int(form.get("category_id"))
    asset.department_id = int(form.get("department_id"))
    asset.user_name = (form.get("user_name") or "").strip() or None

    purchase_date = form.get("purchase_date")
    asset.purchase_date = (
        datetime.strptime(purchase_date, "%Y-%m-%d").date()
        if purchase_date
        else None
    )

    asset.value = float(form.get("value") or 0)
    asset.status = form.get("status") or "active"
    asset.location = (form.get("location") or "").strip() or None
    asset.notes = (form.get("notes") or "").strip() or None

@bp.route("/assets", methods=["GET", "POST"])
@login_required
def list_assets():
    """List assets and create a new asset in the live database."""
    if request.method == "POST":
        error = _validate_asset_form(request.form)
        if error:
            flash(error, "error")
            return redirect(url_for("assets.list_assets") + "#asset-form")

        asset = Asset()
        _apply_form(asset, request.form)
        db.session.add(asset)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Không thể tạo tài sản. Vui lòng kiểm tra dữ liệu trùng lặp.", "error")
            return redirect(url_for("assets.list_assets") + "#asset-form")

        flash(f"Đã thêm tài sản {asset.asset_code} thành công.", "success")
        return redirect(url_for("assets.list_assets"))

    query = request.args.get("q", "").strip()
    category_filter = request.args.get("category_id")
    department_filter = request.args.get("department_id")
    status_filter = request.args.get("status")

    items = Asset.query
    if query:
        items = items.filter(
            (Asset.name.ilike(f"%{query}%"))
            | (Asset.asset_code.ilike(f"%{query}%"))
            | (Asset.user_name.ilike(f"%{query}%"))
        )
    if category_filter:
        try:
            category_filter = int(category_filter)
        except ValueError:
            flash("Bộ lọc danh mục không hợp lệ.", "error")
            return redirect(url_for("assets.list_assets"))
        items = items.filter_by(category_id=category_filter)
    if department_filter:
        try:
            department_filter = int(department_filter)
        except ValueError:
            flash("Bộ lọc phòng ban không hợp lệ.", "error")
            return redirect(url_for("assets.list_assets"))
        items = items.filter_by(department_id=department_filter)
    if status_filter:
        if status_filter not in dict(STATUS_OPTIONS):
            flash("Bộ lọc trạng thái không hợp lệ.", "error")
            return redirect(url_for("assets.list_assets"))
        items = items.filter_by(status=status_filter)

    items = items.order_by(Asset.id.desc()).all()

    return render_template(
        "assets.html",
        assets=items,
        total_assets=Asset.query.count(),
        active_assets=Asset.query.filter_by(status="active").count(),
        repair_assets=Asset.query.filter_by(status="repair").count(),
        disposal_assets=Asset.query.filter_by(status="disposal").count(),
        total_value=db.session.query(db.func.coalesce(db.func.sum(Asset.value), 0)).scalar() or 0,
        **_asset_form_data(),
    )


@bp.route("/assets/<int:asset_id>")
@login_required
def get_asset(asset_id):
    """Display asset detail page."""
    asset = db.session.get(Asset, asset_id)
    if asset is None:
        abort(404)
    return render_template("asset_detail.html", asset=asset)


@bp.route("/assets/<int:asset_id>/edit", methods=["POST"])
@login_required
def update_asset(asset_id):
    """Update an existing asset record."""
    asset = db.session.get(Asset, asset_id)
    if asset is None:
        abort(404)
    error = _validate_asset_form(request.form, asset)
    if error:
        flash(error, "error")
        return redirect(url_for("assets.list_assets") + f"#asset-{asset.id}")

    _apply_form(asset, request.form)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("Không thể cập nhật tài sản. Vui lòng kiểm tra dữ liệu.", "error")
        return redirect(url_for("assets.list_assets"))

    flash(f"Đã cập nhật tài sản {asset.asset_code}.", "success")
    return redirect(url_for("assets.list_assets"))


@bp.route("/assets/<int:asset_id>/delete", methods=["POST"])
@login_required
def delete_asset(asset_id):
    """Delete an asset record when it is not referenced by a transaction."""
    asset = db.session.get(Asset, asset_id)
    if asset is None:
        abort(404)
    asset_code = asset.asset_code
    db.session.delete(asset)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash(
            f"Không thể xóa {asset_code} vì tài sản đã phát sinh nghiệp vụ liên quan. "
            "Hãy chuyển trạng thái hoặc xử lý các nghiệp vụ liên quan trước.",
            "error",
        )
        return redirect(url_for("assets.list_assets"))

    flash(f"Đã xóa tài sản {asset_code}.", "success")
    return redirect(url_for("assets.list_assets"))
