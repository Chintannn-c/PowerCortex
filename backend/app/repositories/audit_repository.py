"""
PowerCortex – Audit Repository

Data-access layer for the ``audit_logs`` MongoDB collection.
"""

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..utils.helpers import utcnow


class AuditRepository:
    """Async CRUD for the ``audit_logs`` collection."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db.audit_logs

    async def create(self, log_data: dict) -> dict:
        """Insert an audit log entry."""
        log_data.setdefault("timestamp", utcnow())
        result = await self._collection.insert_one(log_data)
        log_data["_id"] = result.inserted_id
        return log_data

    async def get_logs_for_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict]:
        """Return audit logs for a specific user, newest first."""
        cursor = (
            self._collection.find({"user_id": user_id})
            .sort("timestamp", -1)
            .skip(skip)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)
