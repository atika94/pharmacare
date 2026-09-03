import os
import sqlite3
import tempfile
import unittest

from app import create_app


class MedicineBrowsingTestCase(unittest.TestCase):
    def setUp(self):
        self.database_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.database_file.close()
        os.environ["SQLITE_DB_PATH"] = self.database_file.name
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        connection = sqlite3.connect(self.database_file.name)
        connection.executemany(
            """
            INSERT INTO medicines
                (name, category, manufacturer, price, stock_quantity, description,
                 requires_prescription)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("Paracetamol", "Pain Relief", "Sample Pharma", 100.0, 50, "Painkiller", 0),
                ("Amoxicillin", "Antibiotic", "Health Labs", 75.0, 0, "Prescription antibiotic", 1),
            ],
        )
        connection.commit()
        connection.close()

    def tearDown(self):
        os.unlink(self.database_file.name)
        os.environ.pop("SQLITE_DB_PATH", None)

    def test_lists_medicines(self):
        response = self.client.get("/medicines")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Paracetamol", response.data)
        self.assertIn(b"Amoxicillin", response.data)
        self.assertIn(b"Out of stock", response.data)
        self.assertIn(b"Prescription", response.data)

    def test_search_matches_name_category_and_description(self):
        for query, expected in [
            ("PARA", b"Paracetamol"),
            ("antibiotic", b"Amoxicillin"),
            ("painkiller", b"Paracetamol"),
        ]:
            with self.subTest(query=query):
                response = self.client.get("/medicines", query_string={"q": query})
                self.assertEqual(response.status_code, 200)
                self.assertIn(expected, response.data)

    def test_search_empty_state(self):
        response = self.client.get("/medicines?q=does-not-exist")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No medicines matched your search.", response.data)


if __name__ == "__main__":
    unittest.main()
