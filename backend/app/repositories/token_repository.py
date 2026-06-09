"""
PowerCortex – Token Repository

Data-access layer for the ``refresh_tokens`` MongoDB collection.
"""

from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..utils.helpers import utcnow


class TokenRepository:
    """Async CRUD for the ``refresh_tokens`` collection."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db.refresh_tokens

    async def create(self, token_data: dict) -> dict:
        """Insert a new refresh token document."""
        token_data.setdefault("created_at", utcnow())
        result = await self._collection.insert_one(token_data)
        token_data["_id"] = result.inserted_id
        return token_data

    async def find_by_token(self, token: str) -> Optional[dict]:
        """Look up a refresh token document by its token string."""
        return await self._collection.find_one({"token": token})

    async def find_all_for_user(self, user_id: str) -> list[dict]:
        """Look up all refresh tokens for a given user ID."""
        cursor = self._collection.find({"user_id": user_id}).sort("created_at", -1)
        return await cursor.to_list(length=None)

    async def delete_by_token(self, token: str) -> bool:
        """Delete a single refresh token.  Returns ``True`` if removed."""
        result = await self._collection.delete_one({"token": token})
        return result.deleted_count == 1

    async def delete_all_for_user(self, user_id: str) -> int:
        """Revoke every refresh token belonging to a user.

        Returns the number of tokens removed.
        """
        result = await self._collection.delete_many({"user_id": user_id})
        return result.deleted_count

    async def cleanup_expired(self) -> int:
        """Remove all expired refresh tokens.  Returns count removed."""
        now = utcnow()
        result = await self._collection.delete_many(
            {"expires_at": {"$lt": now}}
        )
        return result.deleted_count
