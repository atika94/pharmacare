from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlite3 import IntegrityError

from app.database.connection import get_connection
from app.models.user import User


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Check required fields
        if not name or not email or not password or not confirm_password:
            flash("All fields are required.", "danger")
            return render_template("auth/register.html")

        # Check password length
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("auth/register.html")

        # Check passwords
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html")

        connection = get_connection()

        if connection is None:
            flash("Database connection failed.", "danger")
            return render_template("auth/register.html")

        cursor = connection.cursor()

        try:
            # Check if email already exists
            cursor.execute(
                "SELECT id FROM users WHERE email = ?",
                (email,)
            )

            existing_user = cursor.fetchone()

            if existing_user:
                flash("Email already registered.", "danger")
                return render_template("auth/register.html")

            # Hash password
            hashed_password = generate_password_hash(password)

            # Create customer account
            cursor.execute(
                """
                INSERT INTO users (name, email, password, role)
                VALUES (?, ?, ?, ?)
                """,
                (name, email, hashed_password, "customer")
            )

            connection.commit()

            flash("Registration successful. You can now log in.", "success")
            return redirect(url_for("auth.login"))

        except IntegrityError:
            connection.rollback()
            flash("Email already registered.", "danger")
        except Exception as e:
            connection.rollback()
            print(f"Registration error: {e}")
            flash("Something went wrong during registration.", "danger")

        finally:
            cursor.close()
            connection.close()

    return render_template("auth/register.html")


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
            cursor.execute(
                """
                SELECT id, name, email, password, role
                FROM users
                WHERE email = ?
                """,
                (email,)
            )

            user_row = cursor.fetchone()
            user_data = dict(user_row) if user_row else None

            if user_data is None:
                flash("Invalid email or password.", "danger")
                return render_template("auth/login.html")

            # Verify hashed password
            if not check_password_hash(user_data["password"], password):
                flash("Invalid email or password.", "danger")
                return render_template("auth/login.html")

            # Create User object
            user = User(
                id=user_data["id"],
                name=user_data["name"],
                email=user_data["email"],
                role=user_data["role"]
            )

            login_user(user)

            flash("Login successful.", "success")

            return redirect(url_for("home"))

        except Exception as e:
            print(f"Login error: {e}")
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