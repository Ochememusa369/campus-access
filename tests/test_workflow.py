import unittest
import requests_store
import workflow

class TestWorkflowStateMachine(unittest.TestCase):
    def setUp(self):
        """Prepares a fresh in-memory database array state before every run."""
        requests_store.clear_store()

    def test_case_2_issue_before_approval_fails_atomically(self):
        """Verify Case 2: Attempting to issue a requested card fails and alters zero fields."""
        record = requests_store.create_request(fellow_id="F001", card_type="visitor")
        req_id = record["id"]
        
        # Enforce that issuing right away throws a RuntimeError
        with self.assertRaises(RuntimeError):
            workflow.issue_card(req_id)
            
        # PROVE IMMUTABILITY: Ensure the record state remains perfectly unchanged
        post_fail_record = requests_store.get_request(req_id)
        self.assertEqual(post_fail_record["status"], "requested")
        self.assertEqual(post_fail_record["approved_by"], "")

    def test_case_3_approve_with_blank_approver(self):
        """Verify Case 3: Reject approval actions containing blank staff entries."""
        record = requests_store.create_request(fellow_id="F001", card_type="visitor")
        req_id = record["id"]
        
        with self.assertRaises(ValueError):
            workflow.approve_request(req_id, approved_by="   ")
            
        post_fail_record = requests_store.get_request(req_id)
        self.assertEqual(post_fail_record["status"], "requested")

    def test_case_4_happy_path_full_workflow(self):
        """Verify Case 4: Smooth execution loop: requested -> approved -> issued -> returned."""
        record = requests_store.create_request(fellow_id="F001", card_type="visitor")
        req_id = record["id"]
        
        # 1. Step: Approve
        workflow.approve_request(req_id, approved_by="M01")
        self.assertEqual(requests_store.get_request(req_id)["status"], "approved")
        
        # 2. Step: Issue
        workflow.issue_card(req_id)
        self.assertEqual(requests_store.get_request(req_id)["status"], "issued")
        
        # 3. Step: Return
        workflow.return_card(req_id)
        self.assertEqual(requests_store.get_request(req_id)["status"], "returned")

    def test_case_5_reject_double_return_and_reissue(self):
        """Verify Case 5: Returned is final; double returns or reissuing are completely blocked."""
        # Advance record completely to returned status
        record = requests_store.create_request(fellow_id="F001", card_type="visitor")
        req_id = record["id"]
        workflow.approve_request(req_id, approved_by="M01")
        workflow.issue_card(req_id)
        workflow.return_card(req_id)
        
        # Attempting a second return must fail
        with self.assertRaises(RuntimeError):
            workflow.return_card(req_id)
            
        # Attempting to re-issue from returned state must fail
        with self.assertRaises(RuntimeError):
            workflow.issue_card(req_id)

if __name__ == "__main__":
    unittest.main()



