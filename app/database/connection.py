# app/database/connection.py
# Provides MySQL database connectivity for PharmaCare.
# Uses mysql-connector-python. No ORM is used.

import os
import mysql.connector
from mysql.connector import Error


def get_connection():
    """
    Creates and returns a new MySQL database connection.
    Reads credentials from environment variables (loaded from .env).
    Returns None if the connection fails.
    """
    try:
        connection = mysql.connector.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            port=int(os.environ.get("DB_PORT", 3306)),
            user=os.environ.get("DB_USER", "root"),
            password=os.environ.get("DB_PASSWORD", ""),
            database=os.environ.get("DB_NAME", "pharmacare")
        )
        return connection
    except Error as e:
        print(f"[Database] Error connecting to MySQL: {e}")
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
        cursor.execute(query, params or ())
        connection.commit()
        return True
    except Error as e:
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
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        return cursor.fetchone()
    except Error as e:
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
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        return cursor.fetchall()
    except Error as e:
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
                id           INT           NOT NULL AUTO_INCREMENT,
                name         VARCHAR(150)  NOT NULL,
                email        VARCHAR(255)  NOT NULL UNIQUE,
                password     VARCHAR(255)  NOT NULL,
                role         ENUM('customer', 'admin') NOT NULL DEFAULT 'customer',
                created_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # ------------------------------------------------------------------
        # medicines table
        # ------------------------------------------------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS medicines (
                id                     INT            NOT NULL AUTO_INCREMENT,
                name                   VARCHAR(200)   NOT NULL,
                category               VARCHAR(100),
                manufacturer           VARCHAR(150),
                price                  DECIMAL(10, 2) NOT NULL,
                stock_quantity         INT            NOT NULL DEFAULT 0,
                expiry_date            DATE,
                description            TEXT,
                requires_prescription  BOOLEAN        NOT NULL DEFAULT FALSE,
                created_at             DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        connection.commit()
        print("[Database] Tables initialised successfully.")

    except Error as e:
        print(f"[Database] Error initialising tables: {e}")
    finally:
        if cursor:
            cursor.close()
        connection.close()
