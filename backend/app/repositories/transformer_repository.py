from typing import Optional, List, Dict
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from ..utils.helpers import utcnow

logger = logging.getLogger("powercortex.repositories.transformer")

class TransformerRepository:
    """Async database operations for the transformers collection."""
    
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db.transformers

    async def get_all(self) -> List[Dict]:
        """Fetch all transformer assets."""
        cursor = self._collection.find({})
        return await cursor.to_list(length=100)

    async def get_by_id(self, id_or_asset_id: str) -> Optional[Dict]:
        """Fetch a single asset by internal MongoDB ObjectId or human asset_id (e.g., T-101)."""
        # Try finding by ObjectId first if it looks like a valid 24-character hex ID
        if len(id_or_asset_id) == 24:
            try:
                doc = await self._collection.find_one({"_id": ObjectId(id_or_asset_id)})
                if doc:
                    return doc
            except Exception:
                logger.debug(f"'{id_or_asset_id}' is not a valid ObjectId, trying asset_id lookup")
        
        # Fallback to query by human asset_id
        return await self._collection.find_one({"asset_id": id_or_asset_id})

    async def get_by_status(self, status: str) -> List[Dict]:
        """Fetch assets matching a specific status (e.g. Warning, Critical)."""
        cursor = self._collection.find({"status": status})
        return await cursor.to_list(length=100)

    async def save(self, transformer_data: dict) -> dict:
        """Insert or replace a transformer asset document."""
        if "_id" in transformer_data and isinstance(transformer_data["_id"], str):
            try:
                transformer_data["_id"] = ObjectId(transformer_data["_id"])
            except Exception:
                logger.debug(f"Could not convert _id '{transformer_data['_id']}' to ObjectId, using as-is")
                
        now = utcnow()
        transformer_data.setdefault("last_updated", now)
        
        if "_id" in transformer_data:
            doc_id = transformer_data["_id"]
            await self._collection.replace_one({"_id": doc_id}, transformer_data, upsert=True)
        else:
            result = await self._collection.insert_one(transformer_data)
            transformer_data["_id"] = result.inserted_id
            
        return transformer_data

    async def update_telemetry(self, asset_id: str, update_fields: dict) -> Optional[dict]:
        """Update telemetry values and predictions for a transformer asset."""
        now = utcnow()
        update_fields["last_updated"] = now
        
        result = await self._collection.find_one_and_update(
            {"asset_id": asset_id},
            {"$set": update_fields},
            return_document=True
        )
        return result

    async def get_dashboard_summary(self) -> Dict[str, int]:
        """Calculate total, healthy, warning, and critical counts."""
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        
        summary = {"total": 0, "healthy": 0, "warning": 0, "critical": 0}
        
        cursor = self._collection.aggregate(pipeline)
        results = await cursor.to_list(length=10)
        
        for r in results:
            status_val = str(r["_id"]).lower() if r["_id"] else ""
            count = r["count"]
            summary["total"] += count
            if status_val == "healthy":
                summary["healthy"] = count
            elif status_val == "warning":
                summary["warning"] = count
            elif status_val == "critical":
                summary["critical"] = count
                
        return summary
