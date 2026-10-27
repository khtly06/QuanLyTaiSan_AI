"""Authentication routes."""

from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import User, db

bp = Blueprint("auth", __name__)
ROLE_LABELS = {
    "admin": "Quản trị viên",
    "manager": "Quản lý tài sản",
    "inspector": "Kiểm kê viên",
    "staff": "Nhân viên",
}


def login_required(view):
    """Protect views behind a valid user session."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if user is None or not user.is_active:
            session.clear()
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def current_user():
    """Fetch the currently signed-in user from the session."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate a user and redirect to the dashboard when valid."""
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash("⚠ Tài khoản hoặc mật khẩu không chính xác.", "error")
            return render_template("login.html", error_message="⚠ Tài khoản hoặc mật khẩu không chính xác."), 401

        if not user.is_active:
            flash("⚠ Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên.", "error")
            return render_template("login.html", error_message="⚠ Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên."), 403

        session.clear()
        session["user_id"] = user.id
        session["username"] = user.username
        session["role"] = user.role
        flash("✓ Đăng nhập thành công.", "success")
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "GET":
        if session.get("user_id"):
            return redirect(url_for("dashboard.dashboard"))
        return render_template("login.html")


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """Logout the current user and destroy the session."""
    session.clear()
    return redirect(url_for("auth.login"))


@bp.route("/profile")
@login_required
def profile():
    """Display the current user's profile information."""
    user = current_user()
    return render_template("profile.html", user=user)


@bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    """Allow a user to change their own password."""
    user = current_user()
    if request.method == "POST":
        current = request.form.get("current_password") or ""
        new_password = request.form.get("new_password") or ""
        confirm = request.form.get("confirm_password") or ""

        if not current or not new_password or not confirm:
            flash("⚠ Vui lòng nhập đầy đủ thông tin.", "error")
            return render_template("change_password.html", user=user, error_message="⚠ Vui lòng nhập đầy đủ thông tin."), 400

        if not check_password_hash(user.password_hash, current):
            flash("⚠ Mật khẩu hiện tại không chính xác.", "error")
            return render_template("change_password.html", user=user, error_message="⚠ Mật khẩu hiện tại không chính xác."), 400

        if len(new_password) < 12:
            flash("⚠ Mật khẩu mới phải có ít nhất 12 ký tự.", "error")
            return render_template("change_password.html", user=user, error_message="⚠ Mật khẩu mới phải có ít nhất 12 ký tự."), 400

        if new_password != confirm:
            flash("⚠ Xác nhận mật khẩu mới không khớp.", "error")
            return render_template("change_password.html", user=user, error_message="⚠ Xác nhận mật khẩu mới không khớp."), 400

        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        flash("✓ Đổi mật khẩu thành công.", "success")
        return redirect(url_for("auth.change_password"))

    return render_template("change_password.html", user=user)


@bp.route("/users", methods=["GET", "POST"])
@login_required
def users():
    """List accounts and create a user with a validated role."""
    user = current_user()
    if user is None or not user.is_admin:
        return redirect(url_for("dashboard.dashboard"))
    error = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip()
        full_name = (request.form.get("full_name") or "").strip()
        password = request.form.get("password") or ""
        role = request.form.get("role") or ""
        if not all((username, email, full_name, password)) or role not in ROLE_LABELS:
            error = "Vui lòng nhập đầy đủ thông tin và chọn vai trò hợp lệ."
        elif len(password) < 12:
            error = "Mật khẩu phải có ít nhất 12 ký tự."
        else:
            db.session.add(
                User(
                    username=username,
                    email=email,
                    full_name=full_name,
                    password_hash=generate_password_hash(password),
                    role=role,
                    is_active=True,
                )
            )
            try:
                db.session.commit()
                return redirect(url_for("auth.users"))
            except IntegrityError:
                db.session.rollback()
                error = "Tên đăng nhập hoặc email đã được sử dụng."
    response = render_template(
        "users.html",
        users=User.query.order_by(User.id.asc()).all(),
        current_user=user,
        roles=ROLE_LABELS,
        error=error,
    )
    return response, 400 if request.method == "POST" and error else 200


@bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@login_required
def toggle_user_active(user_id):
    user = current_user()
    target = db.session.get(User, user_id)
    if target is None:
        abort(404)
    if target.id == user.id:
        flash("Không thể khóa tài khoản đang sử dụng.", "error")
        return redirect(url_for("auth.users"))
    if target.is_active and target.is_admin:
        active_admins = User.query.filter_by(role="admin", is_active=True).count()
        if active_admins <= 1:
            flash("Không thể khóa quản trị viên đang hoạt động cuối cùng.", "error")
            return redirect(url_for("auth.users"))
    target.is_active = not target.is_active
    db.session.commit()
    flash(
        "Đã cập nhật trạng thái tài khoản.",
        "success",
    )
    return redirect(url_for("auth.users"))


@bp.route("/settings")
@login_required
def settings():
    """Display the settings page."""
    user = current_user()
    if user is None or not user.is_admin:
        return redirect(url_for("dashboard.dashboard"))
    return render_template("settings.html", user=user)
