# app/database/connection.py
# Provides SQLite database connectivity for PharmaCare.
# Uses Python's built-in sqlite3 module. No ORM is used.

import os
import sqlite3


def _database_path():
    return os.environ.get("SQLITE_DB_PATH", "pharmacare.db")


def _sqlite_query(query):
    return query.replace("%s", "?")


def get_connection():
    """
    Creates and returns a new SQLite database connection.
    The database file is created automatically when it does not exist.
    """
    try:
        connection = sqlite3.connect(_database_path())
        connection.row_factory = sqlite3.Row
        return connection
    except sqlite3.Error as e:
        print(f"[Database] Error opening SQLite database: {e}")
        return None


def execute_query(query, params=None):
    """
    Executes an INSERT, UPDATE, or DELETE query.

    Args:
        query  (str): A parameterized SQL query string.
        params (tuple | None): Values to substitute into the query safely.

    Returns:
        True if the query succeeded, False otherwise.
    """
    connection = get_connection()
    if connection is None:
        return False

    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(_sqlite_query(query), params or ())
        connection.commit()
        return True
    except sqlite3.Error as e:
        print(f"[Database] Query error: {e}")
        connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        connection.close()


def fetch_one(query, params=None):
    """
    Executes a SELECT query and returns the first matching row as a dict.

    Args:
        query  (str): A parameterized SQL query string.
        params (tuple | None): Values to substitute into the query safely.

    Returns:
        dict | None: The first row as a dictionary, or None if no result.
    """
    connection = get_connection()
    if connection is None:
        return None

    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(_sqlite_query(query), params or ())
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        print(f"[Database] Fetch error: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        connection.close()


def fetch_all(query, params=None):
    """
    Executes a SELECT query and returns all matching rows as a list of dicts.

    Args:
        query  (str): A parameterized SQL query string.
        params (tuple | None): Values to substitute into the query safely.

    Returns:
        list[dict]: All matching rows, or an empty list on failure.
    """
    connection = get_connection()
    if connection is None:
        return []

    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(_sqlite_query(query), params or ())
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"[Database] Fetch error: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        connection.close()


def init_db():
    """
    Creates the required database tables if they do not already exist.
    Safe to call every time the application starts — existing data is preserved.
    """
    connection = get_connection()
    if connection is None:
        print("[Database] Could not connect — skipping table initialisation.")
        return

    cursor = None
    try:
        cursor = connection.cursor()

        # ------------------------------------------------------------------
        # users table
        # ------------------------------------------------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id           INTEGER       PRIMARY KEY AUTOINCREMENT,
                name         VARCHAR(150)  NOT NULL,
                email        VARCHAR(255)  NOT NULL UNIQUE,
                password     VARCHAR(255)  NOT NULL,
                role         VARCHAR(20)   NOT NULL DEFAULT 'customer',
                created_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ------------------------------------------------------------------
        # medicines table
        # ------------------------------------------------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS medicines (
                id                     INTEGER        PRIMARY KEY AUTOINCREMENT,
                name                   VARCHAR(200)   NOT NULL,
                category               VARCHAR(100),
                manufacturer           VARCHAR(150),
                price                  DECIMAL(10, 2) NOT NULL,
                stock_quantity         INT            NOT NULL DEFAULT 0,
                expiry_date            DATE,
                description            TEXT,
                requires_prescription  BOOLEAN        NOT NULL DEFAULT 0,
                created_at             DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id              INTEGER       PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER       NOT NULL,
                total_amount    DECIMAL(10, 2) NOT NULL,
                pickup_location VARCHAR(200)  NOT NULL,
                status          VARCHAR(30)   NOT NULL DEFAULT 'pending',
                created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id          INTEGER       PRIMARY KEY AUTOINCREMENT,
                order_id    INTEGER       NOT NULL,
                medicine_id INTEGER       NOT NULL,
                quantity    INTEGER       NOT NULL CHECK (quantity > 0),
                unit_price  DECIMAL(10, 2) NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (medicine_id) REFERENCES medicines (id)
            )
        """)

        connection.commit()
        print("[Database] Tables initialised successfully.")

    except sqlite3.Error as e:
        print(f"[Database] Error initialising tables: {e}")
    finally:
        if cursor:
            cursor.close()
        connection.close()
