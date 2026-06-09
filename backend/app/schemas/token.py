"""
PowerCortex – Token & API Response Schemas

Pydantic v2 schemas for token responses and the standard API envelope.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class RefreshTokenRequest(BaseModel):
    """POST /api/auth/refresh"""

    refresh_token: str = Field(..., min_length=1)


class TokenData(BaseModel):
    """Nested token + user data returned on login / refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    user: dict


class ApiResponse(BaseModel):
    """Standard JSON envelope for every API response."""

    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[list[str]] = None
