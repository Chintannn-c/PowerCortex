"""
PowerCortex – User Router

FastAPI router for user management endpoints:
  GET    /api/users
  GET    /api/users/{id}
  PUT    /api/users/{id}
  DELETE /api/users/{id}
"""

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from ..core.database import get_database
from ..core.dependencies import get_current_user
from ..schemas.user import UserUpdateRequest
from ..services.user_service import UserService

router = APIRouter(
    prefix="/api/v1/users",
    tags=["User Management"],
    dependencies=[Depends(get_current_user)],
)


# ── GET /api/users ─────────────────────────────────────────────
@router.get("/", summary="List all users")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    db = get_database()
    service = UserService(db)
    result = await service.list_users(skip=skip, limit=limit)
    return result


# ── GET /api/users/{id} ───────────────────────────────────────
@router.get("/{user_id}", summary="Get user by ID")
async def get_user(user_id: str):
    db = get_database()
    service = UserService(db)
    result = await service.get_user_by_id(user_id)

    if not result["success"]:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=result,
        )

    return result


# ── PUT /api/users/{id} ───────────────────────────────────────
@router.put("/{user_id}", summary="Update user")
async def update_user(user_id: str, body: UserUpdateRequest):
    db = get_database()
    service = UserService(db)
    result = await service.update_user(
        user_id=user_id,
        update_data=body.model_dump(exclude_unset=True),
    )

    if not result["success"]:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=result,
        )

    return result


# ── DELETE /api/users/{id} ─────────────────────────────────────
@router.delete("/{user_id}", summary="Delete user")
async def delete_user(user_id: str):
    db = get_database()
    service = UserService(db)
    result = await service.delete_user(user_id)

    if not result["success"]:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=result,
        )

    return result
