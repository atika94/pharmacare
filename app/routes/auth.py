from datetime import datetime
from datetime import timedelta
import re
import secrets
from sqlite3 import IntegrityError

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.database.connection import get_connection
from app.models.user import User
from app.notifications import send_registration_otp
auth_bp = Blueprint("auth", __name__)
ADMIN_EMAIL = "www.admin@gmail.com"
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSWORD_PATTERN = re.compile(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[^A-Za-z\d]).{8,}$")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        if not name or not email or not password or not confirm_password:
            flash("All fields are required.", "danger")
            return render_template("auth/register.html")
        if not EMAIL_PATTERN.fullmatch(email):
            flash("Please enter a valid email address.", "danger")
            return render_template("auth/register.html")
        if not PASSWORD_PATTERN.fullmatch(password):
            flash("Password must be at least 8 characters and include a letter, number, and symbol.", "danger")
            return render_template("auth/register.html")
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html")

        connection = get_connection()
        if connection is None:
            flash("Database connection failed.", "danger")
            return render_template("auth/register.html")
        cursor = connection.cursor()
        otp = f"{secrets.randbelow(10000):04d}"
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        try:
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                flash("Email already registered.", "danger")
                return render_template("auth/register.html")
            cursor.execute(
                """
                INSERT INTO registration_otps
                    (email, name, password, role, otp_hash, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(email) DO UPDATE SET
                    name = excluded.name,
                    password = excluded.password,
                    role = excluded.role,
                    otp_hash = excluded.otp_hash,
                    expires_at = excluded.expires_at
                """,
                (
                    email,
                    name,
                    generate_password_hash(password),
                    "admin" if email == ADMIN_EMAIL else "customer",
                    generate_password_hash(otp),
                    expires_at.strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            connection.commit()
        except Exception as error:
            connection.rollback()
            print(f"Registration preparation error: {error}")
            flash("Something went wrong during registration.", "danger")
            return render_template("auth/register.html")
        finally:
            cursor.close()
            connection.close()
        if not send_registration_otp(email, otp):
            flash("We could not send the verification email. Please try again.", "danger")
            return render_template("auth/register.html")
        session["registration_email"] = email
        flash("A verification code was sent to your email.", "success")
        return redirect(url_for("auth.verify_registration"))
    return render_template("auth/register.html")


@auth_bp.route("/register/verify", methods=["GET", "POST"])
def verify_registration():
    email = session.get("registration_email", "").strip().lower()
    if not email:
        flash("Start registration first.", "warning")
        return redirect(url_for("auth.register"))
    if request.method == "POST":
        otp = request.form.get("otp", "").strip()
        connection = get_connection()
        pending = connection.execute("SELECT * FROM registration_otps WHERE email = ?", (email,)).fetchone()
        if pending is None:
            connection.close()
            flash("This verification request has expired. Register again.", "danger")
            return redirect(url_for("auth.register"))
        expired = datetime.utcnow() > datetime.strptime(pending["expires_at"], "%Y-%m-%d %H:%M:%S")
        valid = len(otp) == 4 and otp.isdigit() and check_password_hash(pending["otp_hash"], otp)
        if expired or not valid:
            connection.close()
            flash("Invalid or expired verification code.", "danger")
            return render_template("auth/verify.html", email=email)
        try:
            connection.execute(
                "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                (pending["name"], pending["email"], pending["password"], pending["role"]),
            )
            connection.execute("DELETE FROM registration_otps WHERE email = ?", (email,))
            connection.commit()
        except IntegrityError:
            connection.rollback()
            flash("Email already registered.", "danger")
            return redirect(url_for("auth.login"))
        finally:
            connection.close()
        session.pop("registration_email", None)
        flash("Email verified. Registration successful. You can now log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/verify.html", email=email)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("auth/login.html")
        connection = get_connection()
        if connection is None:
            flash("Database connection failed.", "danger")
            return render_template("auth/login.html")
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT id, name, email, password, role FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            user_data = dict(row) if row else None
            if user_data is None or not check_password_hash(user_data["password"], password):
                flash("Invalid email or password.", "danger")
                return render_template("auth/login.html")
            user = User(id=user_data["id"], name=user_data["name"], email=user_data["email"], role=user_data["role"])
            login_user(user)
            flash("Login successful.", "success")
            return redirect(url_for("admin.dashboard" if user.is_admin() else "home"))
        except Exception as error:
            print(f"Login error: {error}")
            flash("Something went wrong during login.", "danger")
        finally:
            cursor.close()
            connection.close()
    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


@auth_bp.route("/account/delete", methods=["POST"])
@login_required
def delete_account():
    if current_user.is_admin():
        flash("The administrator account cannot be deleted here.", "warning")
        return redirect(url_for("home"))

    connection = get_connection()
    if connection is None:
        flash("Database connection failed.", "danger")
        return redirect(url_for("home"))

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN")
        connection.execute(
            """
            DELETE FROM order_items
            WHERE order_id IN (SELECT id FROM orders WHERE user_id = ?)
            """,
            (current_user.id,),
        )
        connection.execute("DELETE FROM orders WHERE user_id = ?", (current_user.id,))
        connection.execute("DELETE FROM registration_otps WHERE email = ?", (current_user.email,))
        connection.execute("DELETE FROM users WHERE id = ?", (current_user.id,))
        connection.commit()
    except Exception:
        connection.rollback()
        current_app.logger.exception("Account deletion failed for user %s", current_user.id)
        flash("We could not delete your account. Please try again.", "danger")
        return redirect(url_for("home"))
    finally:
        connection.close()

    logout_user()
    flash("Your account has been deleted.", "success")
    return redirect(url_for("home"))
