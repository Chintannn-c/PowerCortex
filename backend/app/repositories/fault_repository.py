from typing import Optional, List, Dict
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone, timedelta
import logging
from ..utils.helpers import utcnow

logger = logging.getLogger("powercortex.repositories.fault")

class FaultRepository:
    """Async database operations for the faults collection."""
    
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db.faults

    async def get_all(self, limit: int = 100) -> List[Dict]:
        """Fetch all faults, sorted by detection time descending."""
        cursor = self._collection.find({}).sort("detected_at", -1)
        return await cursor.to_list(length=limit)

    async def get_by_id(self, id_or_fault_id: str) -> Optional[Dict]:
        """Fetch a single fault by MongoDB ObjectId or human fault_id (e.g. FLT-001)."""
        if len(id_or_fault_id) == 24:
            try:
                doc = await self._collection.find_one({"_id": ObjectId(id_or_fault_id)})
                if doc:
                    return doc
            except Exception:
                logger.debug(f"'{id_or_fault_id}' is not a valid ObjectId, trying fault_id lookup")
        return await self._collection.find_one({"fault_id": id_or_fault_id})

    async def get_active(self, limit: int = 100) -> List[Dict]:
        """Fetch active faults only."""
        cursor = self._collection.find({"status": "Active"}).sort("detected_at", -1)
        return await cursor.to_list(length=limit)

    async def get_history(self, limit: int = 100) -> List[Dict]:
        """Fetch historical (Resolved) faults."""
        cursor = self._collection.find({"status": "Resolved"}).sort("detected_at", -1)
        return await cursor.to_list(length=limit)

    async def get_dashboard_summary(self) -> Dict[str, int]:
        """Get counts for dashboard statistics."""
        # Get count of active faults
        active_count = await self._collection.count_documents({"status": "Active"})
        
        # Get count of resolved today
        now = utcnow()
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        resolved_today = await self._collection.count_documents({
            "status": "Resolved",
            "detected_at": {"$gte": today_start}
        })
        
        # Group active faults by severity
        pipeline = [
            {"$match": {"status": "Active"}},
            {"$group": {"_id": "$severity", "count": {"$sum": 1}}}
        ]
        
        cursor = self._collection.aggregate(pipeline)
        results = await cursor.to_list(length=10)
        
        severities = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for r in results:
            sev_val = str(r["_id"]).lower() if r["_id"] else ""
            if sev_val in severities:
                severities[sev_val] = r["count"]
                
        return {
            "active_faults": active_count,
            "resolved_today": resolved_today,
            **severities
        }

    async def get_timeline(self) -> List[Dict]:
        """Aggregate fault counts grouped by date."""
        pipeline = [
            {
                "$project": {
                    "date_str": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$detected_at"
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": "$date_str",
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"_id": 1}
            }
        ]
        
        cursor = self._collection.aggregate(pipeline)
        results = await cursor.to_list(length=30)
        return [{"date": r["_id"], "count": r["count"]} for r in results]

    async def save(self, fault_data: dict) -> dict:
        """Insert or replace a fault document."""
        if "_id" in fault_data and isinstance(fault_data["_id"], str):
            try:
                fault_data["_id"] = ObjectId(fault_data["_id"])
            except Exception:
                logger.debug(f"Could not convert _id '{fault_data['_id']}' to ObjectId, using as-is")
                
        now = utcnow()
        fault_data.setdefault("detected_at", now)
        
        if "_id" in fault_data:
            doc_id = fault_data["_id"]
            await self._collection.replace_one({"_id": doc_id}, fault_data, upsert=True)
        else:
            result = await self._collection.insert_one(fault_data)
            fault_data["_id"] = result.inserted_id
            
        return fault_data

    async def update_status(self, fault_id: str, new_status: str) -> Optional[dict]:
        """Update fault status (e.g. Active to Resolved)."""
        result = await self._collection.find_one_and_update(
            {"fault_id": fault_id},
            {"$set": {"status": new_status}},
            return_document=True
        )
        return result
