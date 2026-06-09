"""
PowerCortex – Assistant Repository

Data-access layer for the ``assistant_chats`` MongoDB collection.
"""

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Dict
from ..utils.helpers import utcnow

class AssistantRepository:
    """Async CRUD for the ``assistant_chats`` collection."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db.assistant_chats

    async def create(self, chat_data: dict) -> dict:
        """Insert a chat entry."""
        chat_data.setdefault("timestamp", utcnow())
        result = await self._collection.insert_one(chat_data)
        chat_data["_id"] = result.inserted_id
        return chat_data

    async def get_history_for_user(
        self,
        user_id: str,
        limit: int = 50,
    ) -> List[Dict]:
        """Return assistant chat entries for a specific user, newest first."""
        cursor = (
            self._collection.find({"user_id": user_id})
            .sort("timestamp", -1)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)
