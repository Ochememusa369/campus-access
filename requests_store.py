import json
import os

# Allowed values based on requirements contract
ALLOWED_CARD_TYPES = {"visitor", "student", "staff"}
ALLOWED_STATUSES = {"requested", "approved", "issued", "returned"}

# In-memory storage dictionary: maps request_id (str) -> request_dict (dict)
_requests_db = {}


def clear_store():
    """Helper function primarily used by unit tests to clear database state."""
    global _requests_db
    _requests_db.clear()


def _validate_ascii_digits(text: str) -> bool:
    """Ensures characters are strictly ASCII 0-9 (rejects arbitrary Unicode digits)."""
    if not text:
        return False
    for char in text:
        if char < "0" or char > "9":
            return False
    return True


def generate_next_id() -> str:
    """
    Analyzes existing IDs (e.g., 'A001', 'A002') and generates the next sequence.
    Handles restarts safely by extracting the maximum numeric counter.
    """
    if not _requests_db:
        return "A001"
    
    max_numeric_id = 0
    for req_id in _requests_db.keys():
        if len(req_id) >= 4 and req_id.startswith("A"):
            numeric_part = req_id[1:]
            if _validate_ascii_digits(numeric_part):
                max_numeric_id = max(max_numeric_id, int(numeric_part))
                
    next_numeric = max_numeric_id + 1
    return f"A{next_numeric:03d}"


def create_request(fellow_id: str, card_type: str) -> dict:
    """
    Validates inputs and registers a new access card request.
    Raises ValueError if assertions fail. Returns a copy of the new record.
    """
    # Defensive validations FIRST
    if not isinstance(fellow_id, str) or not isinstance(card_type, str):
        raise ValueError("Inputs must be strings.")
        
    sanitized_fellow = fellow_id.strip()
    sanitized_card = card_type.strip().lower()
    
    if not sanitized_fellow:
        raise ValueError("Fellow ID cannot be blank.")
        
    if sanitized_card not in ALLOWED_CARD_TYPES:
        raise ValueError(f"Invalid card type. Must be one of: {', '.join(ALLOWED_CARD_TYPES)}")
        
    # All validations clear -> Generate ID and write safely
    next_id = generate_next_id()
    
    new_record = {
        "id": next_id,
        "fellow_id": sanitized_fellow,
        "card_type": sanitized_card,
        "status": "requested",
        "approved_by": ""
    }
    
    _requests_db[next_id] = new_record
    return new_record.copy()


def get_request(request_id: str) -> dict:
    """
    Looks up a single request by its string ID.
    Returns a copy to prevent unauthorized/accidental mutations outside validation rules.
    """
    if request_id not in _requests_db:
        raise KeyError(f"Request ID '{request_id}' not found.")
    return _requests_db[request_id].copy()


def update_request_internally(request_id: str, updated_record: dict):
    """
    Allows Engineer B's workflow module to write validated status mutations back 
    to storage. It validates the shape before overwriting memory.
    """
    if request_id not in _requests_db:
        raise KeyError("Cannot update a non-existent record.")
    
    # Internal deep structural verification
    if updated_record.get("status") not in ALLOWED_STATUSES:
        raise ValueError("Invalid target status.")
        
    _requests_db[request_id] = updated_record.copy()


def list_all_requests() -> list:
    """Returns a list of all current tracking records."""
    return [record.copy() for record in _requests_db.values()]


def save_requests(filepath: str):
    """Serializes the current database directly into a targeted JSON file securely."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(_requests_db, f, indent=4)


def load_requests(filepath: str):
    """
    Loads JSON from disk. Performs structural and data sanity analysis.
    If validation fails, rejects completely and keeps old memory intact.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Target data store file '{filepath}' does not exist.")
        
    with open(filepath, "r", encoding="utf-8") as f:
        raw_content = f.read().strip()
        if not raw_content:
            raise ValueError("Malformed JSON: Data file is entirely empty.")
            
        try:
            loaded_data = json.loads(raw_content)
        except json.JSONDecodeError as err:
            raise ValueError(f"Malformed JSON layout: {err}")
            
    if not isinstance(loaded_data, dict):
        raise ValueError("Invalid database structural shape. Root must be an object.")
        
    # Temporary staging dict to run full file validation before mutating live state
    temp_db = {}
    
    for req_id, record in loaded_data.items():
        # Validate ID formatting keys
        if not req_id.startswith("A") or not _validate_ascii_digits(req_id[1:]):
            raise ValueError(f"Malformed ID key detected in source file: {req_id}")
            
        required_keys = {"id", "fellow_id", "card_type", "status", "approved_by"}
        if not required_keys.issubset(record.keys()):
            raise ValueError(f"Record {req_id} is missing mandatory information structural keys.")
            
        if record["card_type"] not in ALLOWED_CARD_TYPES:
            raise ValueError(f"Record {req_id} contains an illegal card_type attribute.")
            
        if record["status"] not in ALLOWED_STATUSES:
            raise ValueError(f"Record {req_id} contains an illegal state assignment.")
            
        temp_db[req_id] = record
        
    # Atomic Swap: File checks passed smoothly, overwrite real runtime dataset securely
    global _requests_db
    _requests_db = temp_db
