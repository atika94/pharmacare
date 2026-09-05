import os
import sqlite3
import tempfile
import unittest
from io import BytesIO

from app import create_app
from werkzeug.security import generate_password_hash


class AdminManagementTestCase(unittest.TestCase):
    def setUp(self):
        self.database_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.database_file.close()
        os.environ["SQLITE_DB_PATH"] = self.database_file.name
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        connection = sqlite3.connect(self.database_file.name)
        connection.executemany(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            [
                ("Customer", "customer@example.com", generate_password_hash("secret123"), "customer"),
                ("Admin", "admin@example.com", generate_password_hash("secret123"), "admin"),
            ],
        )
        connection.commit()
        connection.close()

    def tearDown(self):
        os.unlink(self.database_file.name)
        os.environ.pop("SQLITE_DB_PATH", None)

    def login(self, email):
        return self.client.post(
            "/login", data={"email": email, "password": "secret123"}
        )

    def medicine_data(self, name="Ibuprofen", stock="8"):
        return {
            "name": name,
            "category": "Pain Relief",
            "manufacturer": "Sample Pharma",
            "price": "9.99",
            "stock_quantity": stock,
            "expiry_date": "2030-01-01",
            "description": "Pain relief medicine",
        }

    def test_customer_cannot_access_admin_dashboard(self):
        self.login("customer@example.com")
        response = self.client.get("/admin")
        self.assertEqual(response.status_code, 403)

    def test_admin_navigation_is_management_and_tracking_only(self):
        self.login("admin@example.com")
        response = self.client.get("/admin")

        self.assertIn(b"Inventory management", response.data)
        self.assertIn(b"Order tracking", response.data)
        self.assertNotIn(b">Cart<", response.data)
        self.assertNotIn(b">Orders<", response.data)

    def test_admin_can_create_edit_and_delete_medicine(self):
        self.login("admin@example.com")
        create = self.client.post("/admin/medicines/new", data=self.medicine_data())
        self.assertEqual(create.status_code, 302)

        dashboard = self.client.get("/admin")
        self.assertEqual(dashboard.status_code, 200)
        self.assertIn(b"Ibuprofen", dashboard.data)
        self.assertIn(b"Low stock", dashboard.data)

        edit = self.client.post(
            "/admin/medicines/1/edit", data=self.medicine_data(name="Updated Medicine", stock="25")
        )
        self.assertEqual(edit.status_code, 302)
        self.assertIn(b"Updated Medicine", self.client.get("/admin").data)

        delete = self.client.post("/admin/medicines/1/delete")
        self.assertEqual(delete.status_code, 302)
        self.assertNotIn(b"Updated Medicine", self.client.get("/admin").data)

    def test_invalid_medicine_values_are_rejected(self):
        self.login("admin@example.com")
        response = self.client.post(
            "/admin/medicines/new", data=self.medicine_data(stock="-1")
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Stock quantity cannot be negative.", response.data)

    def test_admin_can_upload_medicine_image(self):
        self.login("admin@example.com")
        response = self.client.post(
            "/admin/medicines/new",
            data={**self.medicine_data(), "image": (BytesIO(b"fake image"), "medicine.png")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 302)

        connection = sqlite3.connect(self.database_file.name)
        image_filename = connection.execute(
            "SELECT image_filename FROM medicines WHERE id = 1"
        ).fetchone()[0]
        connection.close()
        self.assertTrue(image_filename.endswith(".png"))
        image_path = os.path.join("app", "static", "images", "medicines", image_filename)
        self.assertTrue(os.path.exists(image_path))
        os.remove(image_path)

    def test_admin_can_see_customer_orders(self):
        connection = sqlite3.connect(self.database_file.name)
        connection.execute(
            "INSERT INTO orders (user_id, total_amount, pickup_location) VALUES (?, ?, ?)",
            (1, 19.98, "Main Street Pharmacy"),
        )
        connection.commit()
        connection.close()

        self.login("admin@example.com")
        response = self.client.get("/admin/orders")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"customer@example.com", response.data)
        self.assertIn(b"Main Street Pharmacy", response.data)

    def test_admin_can_add_medicine_to_cart(self):
        self.login("admin@example.com")
        self.client.post("/admin/medicines/new", data=self.medicine_data())
        response = self.client.post("/cart/add/1")

        self.assertEqual(response.status_code, 302)
        self.assertIn(b"Ibuprofen", self.client.get("/cart").data)


if __name__ == "__main__":
    unittest.main()
