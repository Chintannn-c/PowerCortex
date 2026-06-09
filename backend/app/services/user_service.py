"""
PowerCortex – User Service

Business logic for user profile management and CRUD operations.
"""

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..repositories.user_repository import UserRepository
from ..utils.helpers import serialize_doc, to_object_id


class UserService:
    """User management service."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._repo = UserRepository(db)

    async def get_profile(self, user: dict) -> dict:
        """Return the serialized profile of the currently logged-in user."""
        return {"success": True, "data": serialize_doc(user)}

    async def get_user_by_id(self, user_id: str) -> dict:
        """Fetch a single user by their string ID."""
        oid = to_object_id(user_id)
        if oid is None:
            return {"success": False, "message": "Invalid user ID format"}

        user = await self._repo.find_by_id(oid)
        if user is None:
            return {"success": False, "message": "User not found"}

        return {"success": True, "data": serialize_doc(user)}

    async def list_users(self, skip: int = 0, limit: int = 50) -> dict:
        """Return a paginated list of all users."""
        users = await self._repo.list_users(skip=skip, limit=limit)
        total = await self._repo.count()
        return {
            "success": True,
            "data": {
                "users": [serialize_doc(u) for u in users],
                "total": total,
                "skip": skip,
                "limit": limit,
            },
        }

    async def update_user(self, user_id: str, update_data: dict) -> dict:
        """Update user fields."""
        oid = to_object_id(user_id)
        if oid is None:
            return {"success": False, "message": "Invalid user ID format"}

        # Strip None values so we only update provided fields
        clean_data = {k: v for k, v in update_data.items() if v is not None}
        if not clean_data:
            return {"success": False, "message": "No fields to update"}

        updated = await self._repo.update(oid, clean_data)
        if updated is None:
            return {"success": False, "message": "User not found"}

        return {
            "success": True,
            "message": "User updated successfully",
            "data": serialize_doc(updated),
        }

    async def delete_user(self, user_id: str) -> dict:
        """Permanently delete a user."""
        oid = to_object_id(user_id)
        if oid is None:
            return {"success": False, "message": "Invalid user ID format"}

        deleted = await self._repo.delete(oid)
        if not deleted:
            return {"success": False, "message": "User not found"}

        return {"success": True, "message": "User deleted successfully"}
