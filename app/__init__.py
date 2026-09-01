# app/__init__.py
# Flask application factory for PharmaCare.

from flask import Flask
from dotenv import load_dotenv

# Load environment variables from .env before anything else
load_dotenv()


def create_app():
    """
    Application factory — creates and configures the Flask app.
    """
    app = Flask(__name__)

    # Initialise database tables (CREATE IF NOT EXISTS — safe to call on every start)
    from app.database.connection import init_db
    init_db()

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------

    @app.route("/")
    def home():
        return "PharmaCare — Pharmacy Management System is running."

    @app.route("/db-status")
    def db_status():
        """
        Quick health-check route to confirm MySQL connectivity.
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