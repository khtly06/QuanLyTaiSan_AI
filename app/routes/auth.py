"""Authentication routes."""

from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import User, db

bp = Blueprint("auth", __name__)


def login_required(view):
    """Protect views behind a valid user session."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
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


@bp.route("/logout")
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

        if len(new_password) < 6:
            flash("⚠ Mật khẩu mới phải có ít nhất 6 ký tự.", "error")
            return render_template("change_password.html", user=user, error_message="⚠ Mật khẩu mới phải có ít nhất 6 ký tự."), 400

        if new_password != confirm:
            flash("⚠ Xác nhận mật khẩu mới không khớp.", "error")
            return render_template("change_password.html", user=user, error_message="⚠ Xác nhận mật khẩu mới không khớp."), 400

        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        flash("✓ Đổi mật khẩu thành công.", "success")
        return redirect(url_for("auth.change_password"))

    return render_template("change_password.html", user=user)


@bp.route("/users")
@login_required
def users():
    """Display the list of application users for admin management."""
    user = current_user()
    if user is None or not user.is_admin:
        return redirect(url_for("dashboard.dashboard"))
    return render_template("users.html", users=User.query.order_by(User.id.asc()).all(), current_user=user)


@bp.route("/settings")
@login_required
def settings():
    """Display the settings page."""
    user = current_user()
    return render_template("settings.html", user=user)
