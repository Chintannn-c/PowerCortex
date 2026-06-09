"""
PowerCortex – Auth Request / Response Schemas

Pydantic v2 schemas for authentication endpoints.
"""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """POST /api/auth/register"""

    full_name: str = Field(..., min_length=2, max_length=100, examples=["John Doe"])
    email: EmailStr = Field(..., examples=["john@example.com"])
    password: str = Field(..., min_length=8, examples=["Str0ng@Pass"])
    department: str = Field(default="General", max_length=100, examples=["Operations"])


class LoginRequest(BaseModel):
    """POST /api/auth/login"""

    email: EmailStr = Field(..., examples=["john@example.com"])
    password: str = Field(..., examples=["Str0ng@Pass"])


class ChangePasswordRequest(BaseModel):
    """POST /api/auth/change-password"""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, examples=["N3w@SecurePass"])


class ForgotPasswordRequest(BaseModel):
    """POST /api/auth/forgot-password"""

    email: EmailStr = Field(..., examples=["john@example.com"])


class ResetPasswordRequest(BaseModel):
    """POST /api/auth/reset-password"""

    reset_token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, examples=["N3w@SecurePass"])

class Verify2FARequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)

class Login2FARequest(BaseModel):
    temp_token: str
    code: str = Field(..., min_length=6, max_length=6)
