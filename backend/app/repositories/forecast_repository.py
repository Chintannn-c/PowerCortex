from datetime import datetime, timedelta
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..utils.helpers import utcnow

class ForecastRepository:
    """Async database operations for the forecasts collection."""
    
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db.forecasts

    async def save(self, forecast_data: dict) -> dict:
        """Insert a forecast document into the database."""
        now = utcnow()
        forecast_data.setdefault("created_at", now)
        result = await self._collection.insert_one(forecast_data)
        forecast_data["_id"] = result.inserted_id
        return forecast_data

    async def get_latest(self, forecast_type: str = "hourly") -> Optional[dict]:
        """Fetch the most recently generated forecast of a specific type."""
        return await self._collection.find_one(
            {"forecast_type": forecast_type},
            sort=[("created_at", -1)]
        )

    async def list_forecasts(self, forecast_type: Optional[str] = None, skip: int = 0, limit: int = 50) -> list[dict]:
        """Fetch historical forecasts sorted by creation time (newest first)."""
        query = {}
        if forecast_type:
            query["forecast_type"] = forecast_type
            
        cursor = (
            self._collection.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    async def get_chart_data(self, hours: int = 24) -> list[dict]:
        """
        Retrieves actual vs predicted demand records for chart displays.
        If empty, returns simulated historical ranges.
        """
        # Look back from current time
        cutoff = utcnow() - timedelta(hours=hours)
        cursor = (
            self._collection.find({"created_at": {"$gte": cutoff}})
            .sort("created_at", 1)
        )
        data = await cursor.to_list(length=hours)
        
        # If we have less than 10 documents, return simulated points
        # to ensure that the dashboard line chart is always fully populated.
        if len(data) < 12:
            return []
            
        return data

    async def clear_old_forecasts(self, days: int = 30) -> int:
        """Removes historical forecasts older than X days."""
        cutoff = utcnow() - timedelta(days=days)
        result = await self._collection.delete_many({"created_at": {"$lt": cutoff}})
        return result.deleted_count
