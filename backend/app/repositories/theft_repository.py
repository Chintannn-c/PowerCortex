from typing import Optional, List, Dict
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
import logging

logger = logging.getLogger("powercortex.repositories.theft")

class TheftRepository:
    """Async database operations for the theft_alerts collection."""
    
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db.theft_alerts

    async def save_alert(self, alert_data: dict) -> dict:
        """Insert or replace a theft alert document."""
        # Prevent DuplicateKeyError by checking if consumer_id already exists
        consumer_id = alert_data.get("consumer_id")
        if consumer_id and "_id" not in alert_data:
            existing = await self.get_by_consumer_id(consumer_id)
            if existing:
                alert_data["_id"] = existing["_id"]

        if "_id" in alert_data and isinstance(alert_data["_id"], str):
            try:
                alert_data["_id"] = ObjectId(alert_data["_id"])
            except Exception:
                logger.debug(f"Could not convert _id '{alert_data['_id']}' to ObjectId, using as-is")
                
        if "created_at" not in alert_data:
            alert_data["created_at"] = datetime.now(timezone.utc)
            
        if "_id" in alert_data:
            doc_id = alert_data["_id"]
            await self._collection.replace_one({"_id": doc_id}, alert_data, upsert=True)
        else:
            result = await self._collection.insert_one(alert_data)
            alert_data["_id"] = result.inserted_id
            
        return alert_data

    async def get_by_consumer_id(self, consumer_id: str) -> Optional[dict]:
        """Fetch alert profile by consumer_id."""
        return await self._collection.find_one({"consumer_id": consumer_id})

    async def get_all_suspicious(self, limit: int = 100) -> List[dict]:
        """Fetch all suspicious consumers sorted by probability descending."""
        cursor = self._collection.find({"is_suspicious": True}).sort("theft_probability", -1)
        return await cursor.to_list(length=limit)

    async def get_dashboard_summary(self) -> Dict[str, any]:
        """Get summary counts and averages for the dashboard."""
        suspicious_count = await self._collection.count_documents({
            "is_suspicious": True, 
            "status": "Active"
        })
        high_risk_count = await self._collection.count_documents({
            "risk_level": "High Risk", 
            "status": "Active"
        })
        resolved_count = await self._collection.count_documents({
            "status": "Resolved"
        })
        
        # Calculate average probability of active suspicious consumers
        pipeline = [
            {"$match": {"is_suspicious": True, "status": "Active"}},
            {"$group": {"_id": None, "avg_prob": {"$avg": "$theft_probability"}}}
        ]
        
        avg_prob = 0.0
        cursor = self._collection.aggregate(pipeline)
        results = await cursor.to_list(length=1)
        if results and results[0]["avg_prob"] is not None:
            avg_prob = round(float(results[0]["avg_prob"]), 1)
            
        return {
            "suspicious_count": suspicious_count,
            "high_risk_count": high_risk_count,
            "resolved_count": resolved_count,
            "average_probability": avg_prob
        }

    async def get_risk_distribution(self) -> Dict[str, int]:
        """Get counts grouped by risk level."""
        pipeline = [
            {"$group": {"_id": "$risk_level", "count": {"$sum": 1}}}
        ]
        
        cursor = self._collection.aggregate(pipeline)
        results = await cursor.to_list(length=10)
        
        distribution = {"High Risk": 0, "Medium Risk": 0, "Low Risk": 0, "Normal": 0}
        for r in results:
            risk = str(r["_id"]) if r["_id"] else "Normal"
            if risk in distribution:
                distribution[risk] = r["count"]
                
        return distribution
