"""
PowerCortex – User Model

Pydantic v2 model representing a document in the ``users`` MongoDB collection.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from ..utils.helpers import utcnow


class UserDocument(BaseModel):
    """Schema for a document in the ``users`` collection."""

    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password_hash: str
    department: str = Field(default="General", max_length=100)
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    two_factor_enabled: bool = Field(default=False)
    two_factor_secret: Optional[str] = None
    fcm_tokens: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    model_config = ConfigDict(populate_by_name=True)
