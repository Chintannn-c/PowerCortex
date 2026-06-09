"""
PowerCortex – Audit Log Model

Pydantic v2 model for the ``audit_logs`` MongoDB collection.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from ..utils.helpers import utcnow


class AuditAction(str, Enum):
    """Allowed audit actions."""

    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    REGISTER = "REGISTER"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    PASSWORD_RESET = "PASSWORD_RESET"


class AuditLogDocument(BaseModel):
    """Schema for a document in the ``audit_logs`` collection."""

    user_id: str
    action: AuditAction
    timestamp: datetime = Field(default_factory=utcnow)
    ip_address: str = "0.0.0.0"

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}
