import os
import sqlite3
import tempfile
import unittest

from app import create_app


class AuthenticationTestCase(unittest.TestCase):
    def setUp(self):
        self.database_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.database_file.close()
        os.environ["SQLITE_DB_PATH"] = self.database_file.name
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def tearDown(self):
        os.unlink(self.database_file.name)
        os.environ.pop("SQLITE_DB_PATH", None)

    def register(self, email="customer@example.com", password="TestPassword123"):
        return self.client.post(
            "/register",
            data={
                "name": "Test Customer",
                "email": email,
                "password": password,
                "confirm_password": password,
            },
        )

    def test_registration_hashes_password_and_assigns_customer_role(self):
        response = self.register()
        self.assertEqual(response.status_code, 302)

        connection = sqlite3.connect(self.database_file.name)
        row = connection.execute(
            "SELECT name, email, password, role FROM users"
        ).fetchone()
        connection.close()

        self.assertEqual(row[0:2], ("Test Customer", "customer@example.com"))
        self.assertNotEqual(row[2], "TestPassword123")
        self.assertTrue(row[2].startswith("scrypt:"))
        self.assertEqual(row[3], "customer")

    def test_duplicate_email_is_rejected_case_insensitively(self):
        self.register(email="Customer@Example.com")
        response = self.register(email="customer@example.com")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Email already registered.", response.data)

    def test_invalid_login_uses_generic_message(self):
        self.register()
        response = self.client.post(
            "/login",
            data={"email": "customer@example.com", "password": "wrong"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Invalid email or password.", response.data)

    def test_successful_login_shows_user_and_logout_restores_anonymous_navbar(self):
        self.register()
        response = self.client.post(
            "/login",
            data={"email": "CUSTOMER@EXAMPLE.COM", "password": "TestPassword123"},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome, Test Customer", response.data)
        self.assertIn(b"Logout", response.data)

        response = self.client.get("/logout", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"Welcome, Test Customer", response.data)
        self.assertIn(b"Login", response.data)
        self.assertIn(b"Register", response.data)


if __name__ == "__main__":
    unittest.main()
