import requests_store

def approve_request(request_id: str, approved_by: str):
    """
    Transition: requested -> approved
    Requires a non-empty, non-blank approver identifier.
    """
    if not isinstance(approved_by, str):
        raise ValueError("Approver identifier must be a string.")
        
    sanitized_approver = approved_by.strip()
    if not sanitized_approver:
        raise ValueError("Approver identifier cannot be blank.")
        
    # Fetch current record state (gets a safe independent dictionary copy)
    record = requests_store.get_request(request_id)
    current_status = record["status"]
    
    # State Machine Transition Enforcements
    if current_status != "requested":
        raise RuntimeError(f"Cannot approve a request that is currently '{current_status}'.")
        
    # Mutation phase (Safe because validations are complete)
    record["status"] = "approved"
    record["approved_by"] = sanitized_approver
    
    # Write verified record structural update back to memory
    requests_store.update_request_internally(request_id, record)


def issue_card(request_id: str):
    """
    Transition: approved -> issued
    Strict constraint: 'approved_by' cannot be blank. No state skipping allowed.
    """
    record = requests_store.get_request(request_id)
    current_status = record["status"]
    
    # Checkpoint Case 2 & Contract Rules
    if current_status == "requested":
        raise RuntimeError("Cannot issue card before explicit staff approval.")
    if current_status != "approved":
        raise RuntimeError(f"Cannot issue card from state: '{current_status}'.")
    if not record["approved_by"]:
        raise RuntimeError("Cannot issue card: missing staff approval identity.")
        
    # Mutate and update store
    record["status"] = "issued"
    requests_store.update_request_internally(request_id, record)


def return_card(request_id: str):
    """
    Transition: issued -> returned
    'returned' is final. Double returns or post-return actions are blocked.
    """
    record = requests_store.get_request(request_id)
    current_status = record["status"]
    
    # Checkpoint Case 5 Constraints
    if current_status == "returned":
        raise RuntimeError("Card has already been returned. Operation blocked.")
    if current_status != "issued":
        raise RuntimeError(f"Cannot process card return from current state: '{current_status}'.")
        
    # Mutate and update store
    record["status"] = "returned"
    requests_store.update_request_internally(request_id, record)

