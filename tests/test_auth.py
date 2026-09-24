import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

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

    def register(self, email="customer@example.com", password="TestPassword123!"):
        with patch("app.routes.auth.send_registration_otp") as send_otp:
            response = self.client.post(
                "/register",
                data={
                    "name": "Test Customer",
                    "email": email,
                    "password": password,
                    "confirm_password": password,
                },
            )
            if response.status_code == 302 and response.location.endswith("/register/verify"):
                otp = send_otp.call_args.args[1]
                response = self.client.post("/register/verify", data={"otp": otp})
        return response

    def start_registration(self, email="customer@example.com", password="TestPassword123!"):
        with patch("app.routes.auth.send_registration_otp", return_value=True):
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

    def test_registration_rejects_invalid_email(self):
        response = self.start_registration(email="not-an-email")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Please enter a valid email address.", response.data)

    def test_registration_rejects_weak_passwords(self):
        for password in ("short", "allletters", "NoSymbol123", "NoNumber!", "12345678!"):
            with self.subTest(password=password):
                response = self.start_registration(password=password)
                self.assertEqual(response.status_code, 200)
                self.assertIn(b"Password must be at least 8 characters", response.data)

    def test_registration_accepts_required_password_character_types(self):
        response = self.start_registration(password="ValidPass123!")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/register/verify"))

    def test_registration_requires_email_verification(self):
        response = self.start_registration()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/register/verify"))
        connection = sqlite3.connect(self.database_file.name)
        self.assertIsNotNone(
            connection.execute(
                "SELECT email FROM registration_otps WHERE email = ?",
                ("customer@example.com",),
            ).fetchone()
        )
        self.assertIsNone(
            connection.execute(
                "SELECT id FROM users WHERE email = ?",
                ("customer@example.com",),
            ).fetchone()
        )
        connection.close()

    def test_registration_verification_completes_account(self):
        with patch("app.routes.auth.send_registration_otp") as send_otp:
            response = self.client.post(
                "/register",
                data={
                    "name": "Test Customer",
                    "email": "customer@example.com",
                    "password": "TestPassword123!",
                    "confirm_password": "TestPassword123!",
                },
            )
            otp = send_otp.call_args.args[1]

        response = self.client.post("/register/verify", data={"otp": otp})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/login"))

        connection = sqlite3.connect(self.database_file.name)
        self.assertIsNotNone(
            connection.execute(
                "SELECT id FROM users WHERE email = ?",
                ("customer@example.com",),
            ).fetchone()
        )
        connection.close()

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
            data={"email": "CUSTOMER@EXAMPLE.COM", "password": "TestPassword123!"},
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

    def test_password_reset_requires_email_verification(self):
        self.register()
        with patch("app.routes.auth.send_password_reset_otp") as send_otp:
            response = self.client.post(
                "/forgot-password",
                data={"email": "customer@example.com"},
            )
            self.assertEqual(response.status_code, 302)
            otp = send_otp.call_args.args[1]

        response = self.client.post(
            "/reset-password",
            data={"password": "NewPassword123!", "confirm_password": "NewPassword123!"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/forgot-password"))

        response = self.client.post("/forgot-password/verify", data={"otp": otp})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/reset-password"))

        response = self.client.post(
            "/reset-password",
            data={"password": "NewPassword123!", "confirm_password": "NewPassword123!"},
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.post(
            "/login",
            data={"email": "customer@example.com", "password": "NewPassword123!"},
        )
        self.assertEqual(response.status_code, 302)

    def test_customer_can_delete_account(self):
        self.register()
        self.client.post(
            "/login",
            data={"email": "customer@example.com", "password": "TestPassword123!"},
        )

        response = self.client.post("/account/delete", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Your account has been deleted.", response.data)
        self.assertIn(b"Login", response.data)
        connection = sqlite3.connect(self.database_file.name)
        self.assertIsNone(
            connection.execute(
                "SELECT id FROM users WHERE email = ?",
                ("customer@example.com",),
            ).fetchone()
        )
        connection.close()

    def test_admin_cannot_delete_account(self):
        response = self.register(email="WWW.ADMIN@GMAIL.COM")
        self.assertEqual(response.status_code, 302)
        self.client.post(
            "/login",
            data={"email": "www.admin@gmail.com", "password": "TestPassword123!"},
        )

        response = self.client.post("/account/delete", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"The administrator account cannot be deleted here.", response.data)
        connection = sqlite3.connect(self.database_file.name)
        self.assertIsNotNone(
            connection.execute(
                "SELECT id FROM users WHERE email = ?",
                ("www.admin@gmail.com",),
            ).fetchone()
        )
        connection.close()

    def test_designated_admin_email_gets_admin_role(self):
        response = self.register(email="WWW.ADMIN@GMAIL.COM")
        self.assertEqual(response.status_code, 302)

        connection = sqlite3.connect(self.database_file.name)
        role = connection.execute(
            "SELECT role FROM users WHERE email = ?", ("www.admin@gmail.com",)
        ).fetchone()[0]
        connection.close()

        self.assertEqual(role, "admin")

        response = self.client.post(
            "/login",
            data={"email": "www.admin@gmail.com", "password": "TestPassword123!"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin", response.location)


if __name__ == "__main__":
    unittest.main()
