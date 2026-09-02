from flask import Flask
from dotenv import load_dotenv
from flask_login import LoginManager

load_dotenv()


def create_app():

    app = Flask(__name__)

    # Flask secret key
    app.config["SECRET_KEY"] = "pharmacare-secret-key"

    # -------------------------
    # Flask-Login
    # -------------------------

    login_manager = LoginManager()

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."

    login_manager.init_app(app)

    # -------------------------
    # User Loader
    # -------------------------

    @login_manager.user_loader
    def load_user(user_id):

        from app.database.connection import fetch_one
        from app.models.user import User

        user_data = fetch_one(
            """
            SELECT id, name, email, password, role
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )

        if user_data is None:
            return None

        return User(
            id=user_data["id"],
            name=user_data["name"],
            email=user_data["email"],
            password=user_data["password"],
            role=user_data["role"]
        )

    # -------------------------
    # Database
    # -------------------------

    from app.database.connection import init_db

    init_db()

    # -------------------------
    # Routes
    # -------------------------

    from app.routes.auth import auth_bp

    app.register_blueprint(auth_bp)

    # -------------------------
    # Home
    # -------------------------

    @app.route("/")
    def home():
        return "PharmaCare — Pharmacy Management System is running."

    # -------------------------
    # Database Status
    # -------------------------

    @app.route("/db-status")
    def db_status():

        from app.database.connection import get_connection

        conn = get_connection()

        if conn:
            conn.close()
            return "Database connection: OK", 200

        return "Database connection: FAILED", 500

    return app