import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta
from io import BytesIO

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

    def test_home_delivery_adds_fee_and_generates_invoice(self):
        self.login()
        self.client.post("/cart/add/1")
        response = self.client.post(
            "/checkout",
            data={
                "fulfillment_method": "delivery",
                "delivery_address": "House 10, Main Street",
                "delivery_city": "Lahore",
                "postal_code": "54000",
                "contact_email": "orders@example.com",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/orders/1", response.location)
        connection = sqlite3.connect(self.database_file.name)
        order = connection.execute(
            "SELECT total_amount, delivery_address, delivery_city, postal_code, delivery_fee, contact_email FROM orders"
        ).fetchone()
        connection.close()
        self.assertEqual(order, (62.5, "House 10, Main Street", "Lahore", "54000", 50, "orders@example.com"))

        invoice = self.client.get("/orders/1/invoice")
        self.assertEqual(invoice.status_code, 200)
        self.assertIn(b"Invoice #1", invoice.data)
        self.assertIn(b"PKR 62.50", invoice.data)
        self.assertIn(b"orders@example.com", self.client.get("/orders/1/confirmation").data)

    def test_home_delivery_rejects_invalid_postal_code(self):
        self.login()
        self.client.post("/cart/add/1")
        response = self.client.post(
            "/checkout",
            data={
                "fulfillment_method": "delivery",
                "delivery_address": "House 10, Main Street",
                "delivery_city": "Lahore",
                "postal_code": "5400",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"valid 5-digit Pakistan postal code", response.data)

    def test_prescription_is_required_and_can_be_verified_by_admin(self):
        connection = sqlite3.connect(self.database_file.name)
        connection.execute(
            "UPDATE medicines SET requires_prescription = 1 WHERE id = 1"
        )
        connection.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            ("Admin", "admin@example.com", generate_password_hash("secret123"), "admin"),
        )
        connection.commit()
        connection.close()

        self.login()
        self.client.post("/cart/add/1")
        missing = self.client.post("/checkout", data={"pickup_location": "Main Street"})
        self.assertEqual(missing.status_code, 200)
        self.assertIn(b"prescription file is required", missing.data)

        placed = self.client.post(
            "/checkout",
            data={
                "pickup_location": "Main Street",
                "prescription": (BytesIO(b"prescription"), "doctor.pdf"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(placed.status_code, 302)

        connection = sqlite3.connect(self.database_file.name)
        status = connection.execute("SELECT status FROM orders WHERE id = 1").fetchone()[0]
        connection.close()
        self.assertEqual(status, "pending_verification")

        self.client.get("/logout")
        self.client.post("/login", data={"email": "admin@example.com", "password": "secret123"})
        review = self.client.get("/admin/orders")
        self.assertIn(b"Pending verification", review.data)
        verified = self.client.post("/admin/orders/1/verify")
        self.assertEqual(verified.status_code, 302)

        connection = sqlite3.connect(self.database_file.name)
        status = connection.execute("SELECT status FROM orders WHERE id = 1").fetchone()[0]
        connection.close()
        self.assertEqual(status, "verified")

    def test_unverified_prescription_order_is_cancelled_after_30_minutes(self):
        connection = sqlite3.connect(self.database_file.name)
        connection.execute("UPDATE medicines SET requires_prescription = 1 WHERE id = 1")
        connection.commit()
        connection.close()

        self.login()
        self.client.post("/cart/add/1")
        self.client.post(
            "/checkout",
            data={
                "pickup_location": "Main Street",
                "prescription": (BytesIO(b"prescription"), "doctor.pdf"),
            },
            content_type="multipart/form-data",
        )
        old_time = (datetime.utcnow() - timedelta(minutes=31)).strftime("%Y-%m-%d %H:%M:%S")
        connection = sqlite3.connect(self.database_file.name)
        connection.execute("UPDATE orders SET created_at = ? WHERE id = 1", (old_time,))
        connection.commit()
        connection.close()

        self.client.get("/orders")
        connection = sqlite3.connect(self.database_file.name)
        status = connection.execute("SELECT status FROM orders WHERE id = 1").fetchone()[0]
        stock = connection.execute("SELECT stock_quantity FROM medicines WHERE id = 1").fetchone()[0]
        connection.close()
        self.assertEqual(status, "cancelled")
        self.assertEqual(stock, 3)


if __name__ == "__main__":
    unittest.main()
