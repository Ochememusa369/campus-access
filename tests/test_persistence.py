import unittest
import json
import os
from tempfile import NamedTemporaryFile
import requests_store

class TestPersistence(unittest.TestCase):
    def setUp(self):
        requests_store.clear_store()
        # Create a secure temporary file path that cleans up after the test finishes
        self.temp_file = NamedTemporaryFile(delete=False, mode="w+", encoding="utf-8")
        self.temp_filepath = self.temp_file.name
        self.temp_file.close()

    def tearDown(self):
        """Runs after every single test to delete the temporary file from your disk."""
        if os.path.exists(self.temp_filepath):
            os.remove(self.temp_filepath)

    def test_save_and_reload_valid_data(self):
        """Verify that saving records and reloading them preserves unique ID sequencing across restarts."""
        # 1. Populate data and save
        requests_store.create_request(fellow_id="F001", card_type="visitor")
        requests_store.save_requests(self.temp_filepath)
        
        # 2. Reset the runtime in-memory database to simulate a program restart
        requests_store.clear_store()
        
        # 3. Reload from the file and verify state
        requests_store.load_requests(self.temp_filepath)
        all_records = requests_store.list_all_requests()
        self.assertEqual(len(all_records), 1)
        self.assertEqual(all_records[0]["id"], "A001")
        
        # 4. Check that a new request after reload handles ID sequences safely (becomes A002)
        next_record = requests_store.create_request(fellow_id="F002", card_type="staff")
        self.assertEqual(next_record["id"], "A002")

    def test_reject_corrupted_json_case_7(self):
        """Verify Case 7: Loading broken/malformed JSON strings raises a ValueError."""
        # Write structurally broken JSON syntax to the file
        with open(self.temp_filepath, "w", encoding="utf-8") as f:
            f.write("{ 'invalid_json': broken_value ")
            
        with self.assertRaises(ValueError):
            requests_store.load_requests(self.temp_filepath)

    def test_reject_empty_file(self):
        """Ensure an completely blank database file is caught and rejected."""
        with open(self.temp_filepath, "w", encoding="utf-8") as f:
            f.write("") # Completely empty file
            
        with self.assertRaises(ValueError):
            requests_store.load_requests(self.temp_filepath)

if __name__ == "__main__":
    unittest.main()
