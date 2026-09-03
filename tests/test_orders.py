import os
import sqlite3
import tempfile
import unittest

from app import create_app
from werkzeug.security import generate_password_hash


class OrderFlowTestCase(unittest.TestCase):
    def setUp(self):
        self.database_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.database_file.close()
        os.environ["SQLITE_DB_PATH"] = self.database_file.name
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        connection = sqlite3.connect(self.database_file.name)
        connection.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            ("Customer", "customer@example.com", generate_password_hash("secret123"), "customer"),
        )
        connection.execute(
            "INSERT INTO medicines (name, category, price, stock_quantity) VALUES (?, ?, ?, ?)",
            ("Vitamin C", "Supplement", 12.5, 3),
        )
        connection.commit()
        connection.close()

    def tearDown(self):
        os.unlink(self.database_file.name)
        os.environ.pop("SQLITE_DB_PATH", None)

    def login(self):
        return self.client.post(
            "/login",
            data={"email": "customer@example.com", "password": "secret123"},
        )

    def test_cart_requires_login(self):
        response = self.client.get("/orders")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)

    def test_checkout_creates_order_and_reduces_stock(self):
        self.login()
        self.client.post("/cart/add/1")
        response = self.client.post(
            "/checkout", data={"pickup_location": "Main Street Pharmacy"}
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/orders/1", response.location)

        connection = sqlite3.connect(self.database_file.name)
        stock = connection.execute(
            "SELECT stock_quantity FROM medicines WHERE id = 1"
        ).fetchone()[0]
        order = connection.execute(
            "SELECT user_id, total_amount, pickup_location, status FROM orders"
        ).fetchone()
        item_count = connection.execute("SELECT COUNT(*) FROM order_items").fetchone()[0]
        connection.close()

        self.assertEqual(stock, 2)
        self.assertEqual(order[0], 1)
        self.assertEqual(order[1:4], (12.5, "Main Street Pharmacy", "pending"))
        self.assertEqual(item_count, 1)

    def test_empty_cart_cannot_checkout(self):
        self.login()
        response = self.client.get("/checkout")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/cart", response.location)


if __name__ == "__main__":
    unittest.main()
