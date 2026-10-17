
"""Tests for saving and loading access-card requests."""

import json
import os
import tempfile
import unittest

import requests_store


class TestPersistence(unittest.TestCase):

    def setUp(self):
        requests_store.clear_store()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.filename = os.path.join(self.temp_dir.name, "requests.json")

    def tearDown(self):
        requests_store.clear_store()
        self.temp_dir.cleanup()

    def test_save_and_load_requests(self):
        """Saved requests should be restored with all their fields."""
        created = requests_store.create_request("F001", "visitor")
        requests_store.save_requests(self.filename)

        requests_store.clear_store()
        requests_store.load_requests(self.filename)

        loaded = requests_store.get_request(created["id"])
        self.assertEqual(loaded["fellow_id"], "F001")
        self.assertEqual(loaded["card_type"], "visitor")
        self.assertEqual(loaded["status"], "requested")
        self.assertEqual(loaded["approved_by"], "")

    def test_new_ids_remain_unique_after_loading(self):
        """New IDs should not conflict with IDs loaded from disk."""
        first = requests_store.create_request("F001", "student")
        requests_store.save_requests(self.filename)

        requests_store.clear_store()
        requests_store.load_requests(self.filename)
        second = requests_store.create_request("F002", "staff")

        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(second["id"], "A002")

    def test_malformed_json_is_rejected(self):
        """Malformed JSON must raise an error instead of clearing the store."""
        requests_store.create_request("F001", "visitor")

        with open(self.filename, "w", encoding="utf-8") as file:
            file.write("{this is not valid JSON")

        with self.assertRaises(ValueError):
            requests_store.load_requests(self.filename)

        self.assertEqual(len(requests_store.list_all_requests()), 1)

    def test_duplicate_ids_are_rejected(self):
        """A database containing duplicate request IDs must be rejected."""
        record = {
            "id": "A001",
            "fellow_id": "F001",
            "card_type": "visitor",
            "status": "requested",
            "approved_by": "",
        }

        with open(self.filename, "w", encoding="utf-8") as file:
            json.dump([record, record.copy()], file)

        with self.assertRaises(ValueError):
            requests_store.load_requests(self.filename)

    def test_invalid_record_is_rejected(self):
        """Records with unsupported statuses must not be loaded."""
        record = {
            "id": "A001",
            "fellow_id": "F001",
            "card_type": "visitor",
            "status": "lost",
            "approved_by": "",
        }

        with open(self.filename, "w", encoding="utf-8") as file:
            json.dump([record], file)

        with self.assertRaises(ValueError):
            requests_store.load_requests(self.filename)

    def test_failed_load_preserves_existing_requests(self):
        """A failed load must not replace the current in-memory records."""
        original = requests_store.create_request("F001", "staff")

        invalid_record = {
            "id": "A002",
            "fellow_id": "F002",
            "card_type": "invalid-type",
            "status": "requested",
            "approved_by": "",
        }

        with open(self.filename, "w", encoding="utf-8") as file:
            json.dump([invalid_record], file)

        with self.assertRaises(ValueError):
            requests_store.load_requests(self.filename)

        self.assertEqual(
            requests_store.get_request(original["id"])["fellow_id"],
            "F001",
        )
        self.assertEqual(len(requests_store.list_all_requests()), 1)

    def test_non_list_json_is_rejected(self):
        """The top-level JSON database must be a list."""
        with open(self.filename, "w", encoding="utf-8") as file:
            json.dump({"id": "A001"}, file)

        with self.assertRaises(ValueError):
            requests_store.load_requests(self.filename)


if __name__ == "__main__":
    unittest.main()
