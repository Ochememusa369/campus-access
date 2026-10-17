
"""Tests for registering and retrieving access-card requests."""

import unittest

import requests_store


class TestRegistration(unittest.TestCase):

    def setUp(self):
        requests_store.clear_store()

    def tearDown(self):
        requests_store.clear_store()

    def test_register_visitor_request(self):
        """A visitor request should be created with the correct defaults."""
        record = requests_store.create_request("F001", "visitor")

        self.assertEqual(record["id"], "A001")
        self.assertEqual(record["fellow_id"], "F001")
        self.assertEqual(record["card_type"], "visitor")
        self.assertEqual(record["status"], "requested")
        self.assertEqual(record["approved_by"], "")

    def test_register_student_and_staff_requests(self):
        """Student and staff card types should both be accepted."""
        student = requests_store.create_request("F002", "student")
        staff = requests_store.create_request("F003", "staff")

        self.assertEqual(student["card_type"], "student")
        self.assertEqual(staff["card_type"], "staff")

    def test_blank_fellow_id_is_rejected(self):
        """Blank or whitespace-only fellow IDs must be rejected."""
        for fellow_id in ("", "   ", "\t"):
            with self.subTest(fellow_id=repr(fellow_id)):
                with self.assertRaises(ValueError):
                    requests_store.create_request(fellow_id, "visitor")

        self.assertEqual(requests_store.list_all_requests(), [])

    def test_invalid_card_type_is_rejected(self):
        """Unsupported card types must not create requests."""
        for card_type in ("guest", "contractor", "", "VISITOR-PLUS"):
            with self.subTest(card_type=card_type):
                with self.assertRaises(ValueError):
                    requests_store.create_request("F001", card_type)

        self.assertEqual(requests_store.list_all_requests(), [])

    def test_request_ids_are_unique(self):
        """Each newly registered request should receive a different ID."""
        first = requests_store.create_request("F001", "visitor")
        second = requests_store.create_request("F002", "student")
        third = requests_store.create_request("F003", "staff")

        self.assertEqual(
            [first["id"], second["id"], third["id"]],
            ["A001", "A002", "A003"],
        )

    def test_fellow_id_is_trimmed(self):
        """Leading and trailing spaces should be removed from fellow IDs."""
        record = requests_store.create_request("  F004  ", "student")

        self.assertEqual(record["fellow_id"], "F004")

    def test_get_request_returns_correct_record(self):
        """A request should be retrievable by its ID."""
        created = requests_store.create_request("F005", "staff")

        retrieved = requests_store.get_request(created["id"])

        self.assertEqual(retrieved, created)

    def test_unknown_request_id_is_rejected(self):
        """A well-formed but unknown ID should raise KeyError."""
        with self.assertRaises(KeyError):
            requests_store.get_request("A999")

    def test_malformed_request_id_is_rejected(self):
        """Malformed IDs, including non-ASCII digits, should be rejected."""
        invalid_ids = ["", "A1", "B001", "A00X", "A００１"]

        for request_id in invalid_ids:
            with self.subTest(request_id=request_id):
                with self.assertRaises(ValueError):
                    requests_store.get_request(request_id)

    def test_returned_record_does_not_change_stored_record(self):
        """Editing a returned dictionary should not alter stored data."""
        created = requests_store.create_request("F006", "visitor")
        created["fellow_id"] = "CHANGED"

        stored = requests_store.get_request("A001")
        self.assertEqual(stored["fellow_id"], "F006")


if __name__ == "__main__":
    unittest.main()
