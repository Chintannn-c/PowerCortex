"""
PowerCortex – Auth Router

FastAPI router for all authentication endpoints:
  POST /api/auth/register
  POST /api/auth/login
  POST /api/auth/refresh
  POST /api/auth/logout
  POST /api/auth/change-password
  POST /api/auth/forgot-password
  POST /api/auth/reset-password
  GET  /api/auth/me
"""

from fastapi import APIRouter, Depends, Request, status, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..core.database import get_database
from ..core.dependencies import get_current_user
from ..core.rate_limiter import limiter
from ..schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    Verify2FARequest,
    Login2FARequest,
)
from ..schemas.token import RefreshTokenRequest
from ..services.auth_service import AuthService
from ..utils.helpers import serialize_doc

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


def _get_client_ip(request: Request) -> str:
    """Extract the client IP from the request (handles reverse-proxy headers)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "0.0.0.0"


# ── POST /api/auth/register ───────────────────────────────────
@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
@limiter.limit("5/minute")
async def register(body: RegisterRequest, request: Request):
    db = get_database()
    service = AuthService(db)
    result = await service.register(
        full_name=body.full_name,
        email=body.email,
        password=body.password,
        department=body.department,
        ip_address=_get_client_ip(request),
    )

    if not result["success"]:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=result,
        )

    return {
        "success": True,
        "message": "Registration successful",
        "data": result["user"],
    }


# ── POST /api/auth/login ──────────────────────────────────────
@router.post("/login", summary="User login")
@limiter.limit("10/minute")
async def login(body: LoginRequest, request: Request):
    db = get_database()
    service = AuthService(db)
    
    user_agent = request.headers.get("user-agent", "Unknown Device")
    
    result = await service.login(
        email=body.email,
        password=body.password,
        ip_address=_get_client_ip(request),
        device_info=user_agent,
    )

    if not result["success"]:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=result,
        )

    return result


# ── POST /api/auth/refresh ────────────────────────────────────
@router.post("/refresh", summary="Refresh access token")
async def refresh_token(body: RefreshTokenRequest):
    db = get_database()
    service = AuthService(db)
    result = await service.refresh_access_token(body.refresh_token)

    if not result["success"]:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=result,
        )

    return result


# ── POST /api/auth/logout ─────────────────────────────────────
@router.post("/logout", summary="Logout (revoke refresh token)")
async def logout(
    body: RefreshTokenRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = get_database()
    service = AuthService(db)
    result = await service.logout(
        refresh_token_str=body.refresh_token,
        user_id=str(current_user["_id"]),
        ip_address=_get_client_ip(request),
    )
    return result


# ── POST /api/auth/change-password ─────────────────────────────
@router.post("/change-password", summary="Change password")
async def change_password(
    body: ChangePasswordRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = get_database()
    service = AuthService(db)
    result = await service.change_password(
        user=current_user,
        current_password=body.current_password,
        new_password=body.new_password,
        ip_address=_get_client_ip(request),
    )

    if not result["success"]:
        code = status.HTTP_400_BAD_REQUEST
        return JSONResponse(status_code=code, content=result)

    return result


# ── POST /api/auth/forgot-password ─────────────────────────────
@router.post("/forgot-password", summary="Request password reset token")
@limiter.limit("3/minute")
async def forgot_password(body: ForgotPasswordRequest, request: Request):
    db = get_database()
    service = AuthService(db)
    result = await service.forgot_password(email=body.email)
    return result


# ── POST /api/auth/verify-reset-code ───────────────────────────
from ..schemas.auth import VerifyResetCodeRequest

@router.post("/verify-reset-code", summary="Verify password reset code")
@limiter.limit("5/minute")
async def verify_reset_code(body: VerifyResetCodeRequest, request: Request):
    db = get_database()
    service = AuthService(db)
    result = await service.verify_reset_token(body.code)
    if not result["success"]:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=result,
        )
    return result


# ── POST /api/auth/reset-password ──────────────────────────────
@router.post("/reset-password", summary="Reset password with token")
@limiter.limit("3/minute")
async def reset_password(body: ResetPasswordRequest, request: Request):
    db = get_database()
    service = AuthService(db)
    result = await service.reset_password(
        reset_token_str=body.reset_token,
        new_password=body.new_password,
        ip_address=_get_client_ip(request),
    )

    if not result["success"]:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=result,
        )

    return result


# ── GET /api/auth/me ───────────────────────────────────────────
@router.get("/me", summary="Get current user profile")
async def me(current_user: dict = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return {"success": True, "data": serialize_doc(current_user)}


# ── GET /api/auth/2fa/setup ───────────────────────────────────
@router.get("/2fa/setup", summary="Setup 2FA")
async def setup_2fa(current_user: dict = Depends(get_current_user)):
    db = get_database()
    service = AuthService(db)
    result = await service.setup_2fa(str(current_user["_id"]), current_user["email"])
    return result

# ── GET /api/auth/2fa/code ────────────────────────────────────
@router.get("/2fa/code", summary="Request 2FA TOTP code via email")
async def get_2fa_code(current_user: dict = Depends(get_current_user)):
    db = get_database()
    service = AuthService(db)
    result = await service.get_current_2fa_code(str(current_user["_id"]))
    if result["success"]:
        from ..services.email_service import EmailService
        EmailService.send_2fa_code(current_user["email"], result["code"])
    # SECURITY: Never return the TOTP code in the API response — deliver via email only
    return {"success": result["success"], "message": "Verification code sent to your registered email."}

# ── POST /api/auth/2fa/verify ─────────────────────────────────
@router.post(
    "/2fa/verify",
    summary="Verify 2FA setup",
)
async def verify_2fa(
    req: Verify2FARequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    """Verify the TOTP code to complete 2FA setup."""
    auth_service = AuthService(db)
    return await auth_service.verify_2fa(str(current_user["_id"]), req.code)

@router.post(
    "/2fa/disable",
    summary="Disable 2FA",
)
async def disable_2fa(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    """Disable two-factor authentication for the user."""
    auth_service = AuthService(db)
    return await auth_service.disable_2fa(str(current_user["_id"]))

# ── POST /api/auth/login/2fa ──────────────────────────────────
@router.post("/login/2fa", summary="Login with 2FA code")
@limiter.limit("5/minute")
async def login_2fa(body: Login2FARequest, request: Request):
    db = get_database()
    service = AuthService(db)
    user_agent = request.headers.get("user-agent", "Unknown Device")
    
    result = await service.login_with_2fa(
        temp_token=body.temp_token,
        otp_code=body.code,
        ip_address=_get_client_ip(request),
        device_info=user_agent,
    )
    if not result["success"]:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=result)
    return result

# ── POST /api/auth/login/2fa/code ──────────────────────────────
class GetLogin2FACodeRequest(BaseModel):
    temp_token: str

@router.post("/login/2fa/code", summary="Get 2FA code via login temp token (for mock email simulation)")
async def get_login_2fa_code(body: GetLogin2FACodeRequest, background_tasks: BackgroundTasks):
    temp_token = body.temp_token
    if not temp_token:
        return JSONResponse(status_code=400, content={"success": False, "message": "Missing temporary authentication token"})
    
    from ..core.security import decode_access_token
    payload = decode_access_token(temp_token)
    if not payload or payload.get("purpose") != "2fa":
        return JSONResponse(status_code=401, content={"success": False, "message": "Invalid or expired temporary session token"})
        
    db = get_database()
    service = AuthService(db)
    user_id = payload.get("sub")
    
    from ..utils.helpers import to_object_id
    user = await service._user_repo._collection.find_one({"_id": to_object_id(user_id)})
    if not user or not user.get("two_factor_secret"):
        return JSONResponse(status_code=400, content={"success": False, "message": "Two-factor verification setup not configured"})
        
    import pyotp
    totp = pyotp.TOTP(user["two_factor_secret"])
    code = totp.now()
    
    from ..services.email_service import EmailService
    background_tasks.add_task(EmailService.send_2fa_code, user["email"], code)
    
    # SECURITY: Never return the TOTP code in the API response — deliver via email only
    return {"success": True, "message": "Verification code sent to your registered email."}
