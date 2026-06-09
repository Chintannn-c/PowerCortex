"""
PowerCortex – User Schemas

Pydantic v2 schemas for user management endpoints.
"""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    """Serialized user returned in API responses."""

    id: str
    full_name: str
    email: str
    department: str
    is_active: bool
    is_verified: bool
    created_at: str
    updated_at: str


class UserUpdateRequest(BaseModel):
    """PUT /api/users/{id}"""

    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
