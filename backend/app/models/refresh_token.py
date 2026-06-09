"""
PowerCortex – Refresh Token Model

Pydantic v2 model for the ``refresh_tokens`` MongoDB collection.
"""

from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field

from ..utils.helpers import utcnow


class RefreshTokenDocument(BaseModel):
    """Schema for a document in the ``refresh_tokens`` collection."""

    user_id: str  # stored as string, converted to ObjectId in the repository
    token: str
    expires_at: datetime
    device_info: Optional[str] = Field(default="Unknown Device")
    ip_address: Optional[str] = Field(default="0.0.0.0")
    created_at: datetime = Field(default_factory=utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}
