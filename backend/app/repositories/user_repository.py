"""
PowerCortex – User Repository

Pure data-access layer for the ``users`` MongoDB collection.
No business logic — only CRUD operations.
"""

from datetime import datetime
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..utils.helpers import utcnow


class UserRepository:
    """Async CRUD for the ``users`` collection."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db.users

    # ── Create ─────────────────────────────────────────────────
    async def create(self, user_data: dict) -> dict:
        """Insert a new user document and return it with ``_id``."""
        now = utcnow()
        user_data.setdefault("created_at", now)
        user_data.setdefault("updated_at", now)
        user_data.setdefault("is_active", True)
        user_data.setdefault("is_verified", False)

        result = await self._collection.insert_one(user_data)
        user_data["_id"] = result.inserted_id
        return user_data

    # ── Read ───────────────────────────────────────────────────
    async def find_by_email(self, email: str) -> Optional[dict]:
        """Find a single user by email (case-insensitive)."""
        return await self._collection.find_one(
            {"email": email.lower().strip()}
        )

    async def find_by_id(self, user_id: ObjectId) -> Optional[dict]:
        """Find a single user by ``_id``."""
        return await self._collection.find_one({"_id": user_id})

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict]:
        """Return a paginated list of users (newest first)."""
        cursor = (
            self._collection.find()
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    async def count(self) -> int:
        """Return total number of user documents."""
        return await self._collection.count_documents({})

    # ── Update ─────────────────────────────────────────────────
    async def update(self, user_id: ObjectId, update_data: dict) -> Optional[dict]:
        """Update specific fields on a user and return the updated document."""
        update_data["updated_at"] = utcnow()
        result = await self._collection.find_one_and_update(
            {"_id": user_id},
            {"$set": update_data},
            return_document=True,
        )
        return result

    async def update_password(self, user_id: ObjectId, password_hash: str) -> bool:
        """Update only the password hash."""
        result = await self._collection.update_one(
            {"_id": user_id},
            {"$set": {"password_hash": password_hash, "updated_at": utcnow()}},
        )
        return result.modified_count == 1

    # ── Delete ─────────────────────────────────────────────────
    async def delete(self, user_id: ObjectId) -> bool:
        """Delete a user document.  Returns ``True`` if a document was removed."""
        result = await self._collection.delete_one({"_id": user_id})
        return result.deleted_count == 1
