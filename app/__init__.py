# app/__init__.py
# Flask application factory for PharmaCare.

import os

from flask import Flask
from dotenv import load_dotenv
from flask_login import LoginManager

# Load environment variables from .env before anything else
load_dotenv()


def create_app():
    """
    Application factory — creates and configures the Flask app.
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "development-only-secret-key")
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from app.database.connection import fetch_one
        from app.models.user import User

        user_data = fetch_one(
            """
            SELECT id, name, email, role
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        )

        if user_data is None:
            return None

        return User(
            id=user_data["id"],
            name=user_data["name"],
            email=user_data["email"],
            role=user_data["role"]
        )

    # Initialise database tables (CREATE IF NOT EXISTS — safe to call on every start)
    from app.database.connection import init_db
    init_db()

    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.routes.medicines import medicines_bp
    app.register_blueprint(medicines_bp)

    from app.routes.orders import orders_bp
    app.register_blueprint(orders_bp)

    from app.routes.admin import admin_bp
    app.register_blueprint(admin_bp)
    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------

    @app.route("/")
    def home():
        from flask import render_template
        from app.database.connection import fetch_all

        featured_medicines = fetch_all(
            """
            SELECT id, name, category, price, stock_quantity, image_filename
            FROM medicines
            WHERE stock_quantity > 0
            ORDER BY name COLLATE NOCASE
            LIMIT 6
            """
        )

        return render_template("home.html", featured_medicines=featured_medicines)

    @app.route("/db-status")
    def db_status():
        """
        Quick health-check route to confirm SQLite connectivity.
        Returns a plain-text status message.
        Remove or restrict this route in production.
        """
        from app.database.connection import get_connection
        conn = get_connection()
        if conn:
            conn.close()
            return "Database connection: OK", 200
        return "Database connection: FAILED", 500

    return app