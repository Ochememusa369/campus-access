
"""Storage, validation, ID generation, and JSON persistence for access-card requests."""

import json
import re

_requests = {}
_next_id = 1

VALID_CARD_TYPES = {"visitor", "student", "staff"}
VALID_STATUSES = {"requested", "approved", "issued", "returned"}

REQUIRED_FIELDS = {
    "id",
    "fellow_id",
    "card_type",
    "status",
    "approved_by",
}

ID_PATTERN = re.compile(r"A[0-9]{3,}\Z")


def clear_store():
    """Clear all records. Useful for tests."""
    global _requests, _next_id
    _requests = {}
    _next_id = 1


def _validate_request_id(request_id):
    """Reject malformed request IDs."""
    if not isinstance(request_id, str) or not ID_PATTERN.fullmatch(request_id):
        raise ValueError("Request ID must look like A001.")

    if int(request_id[1:]) < 1:
        raise ValueError("Request ID must be greater than A000.")


def _validate_record(record):
    """Validate a complete request record."""
    if not isinstance(record, dict):
        raise ValueError("Each request must be a dictionary.")

    if set(record) != REQUIRED_FIELDS:
        raise ValueError(
            "Request must contain exactly: id, fellow_id, card_type, "
            "status, and approved_by."
        )

    _validate_request_id(record["id"])

    if not isinstance(record["fellow_id"], str) or not record["fellow_id"].strip():
        raise ValueError("Fellow ID cannot be blank.")

    if record["card_type"] not in VALID_CARD_TYPES:
        raise ValueError("Invalid card type.")

    if record["status"] not in VALID_STATUSES:
        raise ValueError("Invalid request status.")

    approver = record["approved_by"]
    if not isinstance(approver, str):
        raise ValueError("Approved by must be a string.")

    if record["status"] in {"approved", "issued", "returned"}:
        if not approver.strip():
            raise ValueError(
                "Approved, issued, and returned requests need an approver."
            )


def create_request(fellow_id, card_type):
    """Create a new request with a unique ID and requested status."""
    global _next_id

    if not isinstance(fellow_id, str) or not fellow_id.strip():
        raise ValueError("Fellow ID cannot be blank.")

    if not isinstance(card_type, str):
        raise ValueError("Card type must be a string.")

    card_type = card_type.strip().lower()
    if card_type not in VALID_CARD_TYPES:
        raise ValueError("Card type must be visitor, student, or staff.")

    request_id = f"A{_next_id:03d}"

    record = {
        "id": request_id,
        "fellow_id": fellow_id.strip(),
        "card_type": card_type,
        "status": "requested",
        "approved_by": "",
    }

    _requests[request_id] = record
    _next_id += 1

    return record.copy()


def get_request(request_id):
    """Return one request without exposing the stored dictionary."""
    _validate_request_id(request_id)

    if request_id not in _requests:
        raise KeyError(f"Request {request_id} was not found.")

    return _requests[request_id].copy()


def list_all_requests():
    """Return copies of all requests."""
    return [record.copy() for record in _requests.values()]


def update_request_internally(request_id, record):
    """Apply one valid workflow transition to an existing request."""
    _validate_request_id(request_id)

    if request_id not in _requests:
        raise KeyError(f"Request {request_id} was not found.")

    _validate_record(record)

    current = _requests[request_id]

    if record["id"] != request_id:
        raise ValueError("Request ID cannot be changed.")

    if record["fellow_id"] != current["fellow_id"]:
        raise ValueError("Fellow ID cannot be changed.")

    if record["card_type"] != current["card_type"]:
        raise ValueError("Card type cannot be changed.")

    allowed_transitions = {
        "requested": "approved",
        "approved": "issued",
        "issued": "returned",
    }

    old_status = current["status"]
    new_status = record["status"]

    if new_status == old_status:
        if record["approved_by"] != current["approved_by"]:
            raise ValueError("Approver cannot be changed without a status transition.")
        raise RuntimeError("The request has not made a valid status transition.")

    if allowed_transitions.get(old_status) != new_status:
        raise RuntimeError(
            f"Cannot change request status from {old_status} to {new_status}."
        )

    if new_status == "approved":
        if not record["approved_by"].strip():
            raise ValueError("An approver is required.")

    elif record["approved_by"] != current["approved_by"]:
        raise ValueError("Approver cannot be changed during this transition.")

    # Update only after all validation succeeds.
    _requests[request_id] = record.copy()


def save_requests(filename):
    """Save requests as JSON."""
    data = list_all_requests()

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def load_requests(filename):
    """Load and validate JSON without replacing existing data on failure."""
    global _requests, _next_id

    with open(filename, "r", encoding="utf-8") as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {filename}: {exc}") from exc

    if not isinstance(data, list):
        raise ValueError("The JSON database must contain a list of requests.")

    # Validate everything in temporary storage before changing the live store.
    loaded_requests = {}

    for record in data:
        _validate_record(record)
        request_id = record["id"]

        if request_id in loaded_requests:
            raise ValueError(f"Duplicate request ID: {request_id}")

        # Store a copy so callers cannot mutate the database through a reference.
        loaded_requests[request_id] = record.copy()

    highest_id = max(
        (int(request_id[1:]) for request_id in loaded_requests),
        default=0,
    )

    # Replace live data only after the entire file has passed validation.
    _requests = loaded_requests
    _next_id = highest_id + 1
