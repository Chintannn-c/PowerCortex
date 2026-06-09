"""
PowerCortex – Helper Utilities

Common utilities shared across the application:
  • ObjectId conversion
  • MongoDB document serialization
  • Password strength validation
"""

import re
from datetime import datetime, timezone

from bson import ObjectId


def to_object_id(value: str) -> ObjectId | None:
    """Safely convert a string to a BSON ``ObjectId``.

    Returns ``None`` if *value* is not a valid 24-hex-char ObjectId string.
    """
    try:
        return ObjectId(value)
    except Exception:
        return None


def serialize_doc(doc: dict) -> dict:
    """Convert a MongoDB document to a JSON-safe dict.

    • ``_id`` → ``"id"`` (string)
    • ``ObjectId`` values → strings
    • ``datetime`` values remain as-is (FastAPI handles ISO serialization)
    • ``password_hash`` is stripped from the output
    """
    if doc is None:
        return {}

    result: dict = {}
    for key, value in doc.items():
        if key == "_id":
            result["id"] = str(value)
        elif key == "password_hash":
            continue  # never expose
        elif isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        else:
            result[key] = value
    return result


def utcnow() -> datetime:
    """Return the current UTC time as a timezone-aware ``datetime``."""
    return datetime.now(timezone.utc)


# ── Password strength validation ──────────────────────────────
_PASSWORD_MIN_LENGTH = 8
_PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#]).{8,}$"
)


def validate_password_strength(password: str) -> list[str]:
    """Return a list of human-readable issues with *password*.

    An empty list means the password is strong enough.
    """
    errors: list[str] = []
    if len(password) < _PASSWORD_MIN_LENGTH:
        errors.append(
            f"Password must be at least {_PASSWORD_MIN_LENGTH} characters"
        )
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one digit")
    if not re.search(r"[@$!%*?&#]", password):
        errors.append(
            "Password must contain at least one special character (@$!%*?&#)"
        )
    return errors
