import unittest
from unittest.mock import patch
import io
import requests_store
import cli

class TestCommandLineInterface(unittest.TestCase):
    def setUp(self):
        """Resets storage array bounds before testing menu runs."""
        requests_store.clear_store()

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_invalid_menu_option_retry_case_8(self, mock_stdout, mock_input):
        """Verify Case 8: Entering a wrong menu option displays feedback and prompts again."""
        # Simulate typing '99' (invalid), then typing '9' to gracefully terminate the application
        mock_input.side_effect = ["99", "9"]

        cli.run_menu()

        # Capture console outputs
        console_output = mock_stdout.getvalue()

        # Verify the menu printed its warning cleanly without crashing out
        self.assertIn("Invalid menu option selection", console_output)
        self.assertIn("Exiting system safely", console_output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_creation_flow_integration(self, mock_stdout, mock_input):
        """Ensure selecting Option 1 maps accurately down to creating an active data record."""
        # User choices sequence:
        # '1' -> Choice (Create)
        # 'F001' -> Fellow ID
        # 'visitor' -> Card type
        # '9' -> Choice (Quit safely)
        mock_input.side_effect = ["1", "F001", "visitor", "9"]

        cli.run_menu()

        # Verify from Engineer A's component store that memory registers the change
        records = requests_store.list_all_requests()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["id"], "A001")
        self.assertEqual(records[0]["fellow_id"], "F001")

if __name__ == "__main__":
    unittest.main()

