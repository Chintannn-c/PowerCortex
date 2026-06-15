"""
PowerCortex – Auth Service

Core authentication business logic:
  • Registration
  • Login / token generation
  • Token refresh
  • Logout (token revocation)
  • Change password
  • Forgot / reset password
"""

from datetime import timedelta
import pyotp

from motor.motor_asyncio import AsyncIOMotorDatabase

from ..core.config import settings
from ..core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from ..models.audit_log import AuditAction
from ..repositories.token_repository import TokenRepository
from ..repositories.user_repository import UserRepository
from ..services.audit_service import AuditService
from ..utils.helpers import serialize_doc, utcnow, validate_password_strength


class AuthService:
    """Authentication and authorisation service."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._user_repo = UserRepository(db)
        self._token_repo = TokenRepository(db)
        self._audit = AuditService(db)

    # ── Register ───────────────────────────────────────────────
    async def register(
        self,
        full_name: str,
        email: str,
        password: str,
        department: str,
        ip_address: str = "0.0.0.0",
    ) -> dict:
        """Create a new user account.

        Returns ``{"success": True, "user": …}`` on success or
        ``{"success": False, "message": …, "errors": …}`` on failure.
        """
        # Validate password strength
        pwd_errors = validate_password_strength(password)
        if pwd_errors:
            return {
                "success": False,
                "message": "Validation failed",
                "errors": pwd_errors,
            }

        # Check for duplicate email
        email_lower = email.lower().strip()
        existing = await self._user_repo.find_by_email(email_lower)
        if existing is not None:
            return {
                "success": False,
                "message": "A user with this email already exists",
            }

        # Persist the user
        user_doc = await self._user_repo.create(
            {
                "full_name": full_name.strip(),
                "email": email_lower,
                "password_hash": hash_password(password),
                "department": department.strip() or "General",
                "is_active": True,
                "is_verified": False,
            }
        )

        await self._audit.log_action(
            str(user_doc["_id"]), AuditAction.REGISTER, ip_address
        )

        return {"success": True, "user": serialize_doc(user_doc)}

    # ── Login ──────────────────────────────────────────────────
    async def login(
        self,
        email: str,
        password: str,
        ip_address: str = "0.0.0.0",
        device_info: str = "Unknown Device",
    ) -> dict:
        """Authenticate a user and return a token pair."""
        user = await self._user_repo.find_by_email(email.lower().strip())
        if user is None or not verify_password(password, user["password_hash"]):
            return {"success": False, "message": "Invalid credentials"}

        if not user.get("is_active", False):
            return {"success": False, "message": "Account is deactivated"}

        user_id_str = str(user["_id"])
        token_payload = {"sub": user_id_str, "email": user["email"]}

        if user.get("two_factor_enabled"):
            temp_token = create_access_token({"sub": user_id_str, "purpose": "2fa"}, expires_delta=timedelta(minutes=5))
            return {
                "success": True,
                "requires_2fa": True,
                "temp_token": temp_token,
            }

        access = create_access_token(token_payload)
        refresh = create_refresh_token(token_payload)

        # Persist refresh token
        expires_at = utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self._token_repo.create(
            {
                "user_id": user_id_str,
                "token": refresh,
                "expires_at": expires_at,
                "device_info": device_info,
                "ip_address": ip_address,
            }
        )

        await self._audit.log_action(user_id_str, AuditAction.LOGIN, ip_address)

        return {
            "success": True,
            "message": "Login successful",
            "data": {
                "access_token": access,
                "refresh_token": refresh,
                "token_type": "Bearer",
                "user": serialize_doc(user),
            },
        }

    async def login_with_2fa(
        self,
        temp_token: str,
        otp_code: str,
        ip_address: str = "0.0.0.0",
        device_info: str = "Unknown Device",
    ) -> dict:
        from ..core.security import decode_access_token
        payload = decode_access_token(temp_token)
        if not payload or payload.get("purpose") != "2fa":
            return {"success": False, "message": "Invalid or expired temp token"}

        from ..utils.helpers import to_object_id
        user_id_str = payload.get("sub", "")
        user_oid = to_object_id(user_id_str)
        user = await self._user_repo._collection.find_one({"_id": user_oid})

        if not user or not user.get("two_factor_enabled") or not user.get("two_factor_secret"):
            return {"success": False, "message": "2FA is not properly configured"}

        totp = pyotp.TOTP(user["two_factor_secret"])
        if not totp.verify(otp_code, valid_window=1):
            return {"success": False, "message": "Invalid or expired 2FA code"}

        token_payload = {"sub": user_id_str, "email": user["email"]}
        access = create_access_token(token_payload)
        refresh = create_refresh_token(token_payload)

        expires_at = utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self._token_repo.create(
            {
                "user_id": user_id_str,
                "token": refresh,
                "expires_at": expires_at,
                "device_info": device_info,
                "ip_address": ip_address,
            }
        )

        await self._audit.log_action(user_id_str, AuditAction.LOGIN, ip_address)

        return {
            "success": True,
            "message": "Login successful",
            "data": {
                "access_token": access,
                "refresh_token": refresh,
                "token_type": "Bearer",
                "user": serialize_doc(user),
            },
        }

    # ── Refresh Token ──────────────────────────────────────────
    async def refresh_access_token(self, refresh_token_str: str) -> dict:
        """Issue a new access token using a valid refresh token."""
        payload = decode_refresh_token(refresh_token_str)
        if payload is None:
            return {"success": False, "message": "Invalid or expired refresh token"}

        # Check the token exists in the DB (not revoked)
        stored = await self._token_repo.find_by_token(refresh_token_str)
        if stored is None:
            return {"success": False, "message": "Refresh token has been revoked"}

        user_id_str = payload.get("sub", "")
        email = payload.get("email", "")
        new_access = create_access_token({"sub": user_id_str, "email": email})

        return {
            "success": True,
            "message": "Token refreshed",
            "data": {
                "access_token": new_access,
                "token_type": "Bearer",
            },
        }

    # ── 2FA ────────────────────────────────────────────────────────
    async def setup_2fa(self, user_id: str, email: str) -> dict:
        secret = pyotp.random_base32()
        from ..utils.helpers import to_object_id
        await self._user_repo._collection.update_one(
            {"_id": to_object_id(user_id)},
            {"$set": {"two_factor_secret": secret}}
        )
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=settings.APP_NAME)
        return {"success": True, "secret": secret, "uri": uri}

    async def get_current_2fa_code(self, user_id: str) -> dict:
        from ..utils.helpers import to_object_id
        user = await self._user_repo._collection.find_one({"_id": to_object_id(user_id)})
        if not user or not user.get("two_factor_secret"):
            return {"success": False, "message": "2FA setup not initiated"}
        totp = pyotp.TOTP(user["two_factor_secret"])
        return {"success": True, "code": totp.now()}

    async def verify_2fa(self, user_id: str, code: str) -> dict:
        from ..utils.helpers import to_object_id
        user = await self._user_repo._collection.find_one({"_id": to_object_id(user_id)})
        if not user or not user.get("two_factor_secret"):
            return {"success": False, "message": "2FA setup not initiated"}

        totp = pyotp.TOTP(user["two_factor_secret"])
        if totp.verify(code, valid_window=1):
            await self._user_repo._collection.update_one(
                {"_id": to_object_id(user_id)},
                {"$set": {"two_factor_enabled": True}}
            )
            return {"success": True, "message": "2FA enabled successfully"}
        return {"success": False, "message": "Invalid 2FA code"}

    async def disable_2fa(self, user_id: str) -> dict:
        from ..utils.helpers import to_object_id
        await self._user_repo._collection.update_one(
            {"_id": to_object_id(user_id)},
            {"$set": {"two_factor_enabled": False, "two_factor_secret": None}}
        )
        return {"success": True, "message": "2FA successfully disabled."}

    # ── Logout ─────────────────────────────────────────────────
    async def logout(
        self,
        refresh_token_str: str,
        user_id: str,
        ip_address: str = "0.0.0.0",
    ) -> dict:
        """Revoke a refresh token (single-device logout)."""
        await self._token_repo.delete_by_token(refresh_token_str)
        await self._audit.log_action(user_id, AuditAction.LOGOUT, ip_address)
        return {"success": True, "message": "Logged out successfully"}

    # ── Change Password ────────────────────────────────────────
    async def change_password(
        self,
        user: dict,
        current_password: str,
        new_password: str,
        ip_address: str = "0.0.0.0",
    ) -> dict:
        """Change the password for an authenticated user."""
        if not verify_password(current_password, user["password_hash"]):
            return {"success": False, "message": "Current password is incorrect"}

        pwd_errors = validate_password_strength(new_password)
        if pwd_errors:
            return {
                "success": False,
                "message": "Validation failed",
                "errors": pwd_errors,
            }

        user_id = user["_id"]
        await self._user_repo.update_password(user_id, hash_password(new_password))

        # Revoke all existing refresh tokens (force re-login on other devices)
        await self._token_repo.delete_all_for_user(str(user_id))

        await self._audit.log_action(
            str(user_id), AuditAction.PASSWORD_CHANGE, ip_address
        )

        return {"success": True, "message": "Password changed successfully"}

    # ── Forgot Password ────────────────────────────────────────
    async def forgot_password(self, email: str) -> dict:
        """Generate a password-reset token.

        In production, the token would be sent via email / SMS.
        For development, it is returned directly in the response.
        """
        user = await self._user_repo.find_by_email(email.lower().strip())
        if user is None:
            # Do not reveal whether the email exists
            return {
                "success": True,
                "message": "If the email exists, a reset token has been generated",
            }

        user_id_str = str(user["_id"])
        reset_token = create_refresh_token(
            {"sub": user_id_str, "email": user["email"], "purpose": "reset"},
            expires_delta=timedelta(minutes=15),
        )

        # Persist as a short-lived refresh token
        await self._token_repo.create(
            {
                "user_id": user_id_str,
                "token": reset_token,
                "expires_at": utcnow() + timedelta(minutes=15),
            }
        )

        from ..services.email_service import EmailService
        EmailService.send_reset_token(user["email"], reset_token)

        response = {
            "success": True,
            "message": "If the email exists, a password reset link has been sent.",
        }
        if settings.DEBUG:
            response["token"] = reset_token
            
        return response

    # ── Reset Password ─────────────────────────────────────────
    async def reset_password(
        self,
        reset_token_str: str,
        new_password: str,
        ip_address: str = "0.0.0.0",
    ) -> dict:
        """Reset a user's password using a valid reset token."""
        payload = decode_refresh_token(reset_token_str)
        if payload is None:
            return {"success": False, "message": "Invalid or expired reset token"}

        # Must still be in the DB
        stored = await self._token_repo.find_by_token(reset_token_str)
        if stored is None:
            return {"success": False, "message": "Reset token has been used or revoked"}

        pwd_errors = validate_password_strength(new_password)
        if pwd_errors:
            return {
                "success": False,
                "message": "Validation failed",
                "errors": pwd_errors,
            }

        from ..utils.helpers import to_object_id

        user_id_str = payload.get("sub", "")
        user_oid = to_object_id(user_id_str)
        if user_oid is None:
            return {"success": False, "message": "Invalid token payload"}

        await self._user_repo.update_password(user_oid, hash_password(new_password))

        # Consume the reset token
        await self._token_repo.delete_by_token(reset_token_str)
        # Revoke all other refresh tokens
        await self._token_repo.delete_all_for_user(user_id_str)

        await self._audit.log_action(
            user_id_str, AuditAction.PASSWORD_RESET, ip_address
        )

        return {"success": True, "message": "Password reset successfully"}
