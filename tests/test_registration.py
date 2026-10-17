import unittest
# Assuming your module is named requests_store or registration
import requests_store

class TestRegistration(unittest.TestCase):
    def setUp(self):
        """Runs before every single test to give you a pristine database state."""
        requests_store.clear_store()

    def test_valid_creation_case_1(self):
        """Verify Case 1: Creating a valid visitor request assigns 'A001' and 'requested' status."""
        record = requests_store.create_request(fellow_id="F001", card_type="visitor")
        
        self.assertEqual(record["id"], "A001")
        self.assertEqual(record["fellow_id"], "F001")
        self.assertEqual(record["card_type"], "visitor")
        self.assertEqual(record["status"], "requested")
        self.assertEqual(record["approved_by"], "")

    def test_reject_blank_fellow_id(self):
        """Ensure creation fails with a ValueError if the fellow ID is empty or spaces."""
        with self.assertRaises(ValueError):
            requests_store.create_request(fellow_id="   ", card_type="student")

    def test_reject_invalid_card_type(self):
        """Ensure creation fails with a ValueError if card type is unrecognized."""
        with self.assertRaises(ValueError):
            requests_store.create_request(fellow_id="F002", card_type="admin")

    def test_unique_id_incrementation(self):
        """Ensure consecutive creations increment IDs correctly (A001 -> A002)."""
        first = requests_store.create_request(fellow_id="F001", card_type="visitor")
        second = requests_store.create_request(fellow_id="F002", card_type="student")
        
        self.assertEqual(first["id"], "A001")
        self.assertEqual(second["id"], "A002")

if __name__ == "__main__":
    unittest.main()
