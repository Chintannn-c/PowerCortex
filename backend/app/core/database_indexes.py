import asyncio
import logging
from pymongo import ASCENDING, DESCENDING
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

logger = logging.getLogger(__name__)

async def setup_database_indexes():
    """
    Ensure all necessary MongoDB collections have optimal indexing for
    query efficiency, aggregation performance, and scale.
    """
    logger.info("Starting MongoDB Index Optimization...")
    
    # Connect directly for admin setup
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    
    try:
        # Users Collection
        logger.info("Creating indexes for: users")
        await db.users.create_index([("email", ASCENDING)], unique=True, background=True)
        await db.users.create_index([("phone", ASCENDING)], unique=True, sparse=True, background=True)
        await db.users.create_index([("role", ASCENDING)], background=True)
        
        # Grid Demand Collection
        logger.info("Creating indexes for: grid_demand")
        await db.grid_demand.create_index([("timestamp", DESCENDING)], background=True)
        await db.grid_demand.create_index([("region", ASCENDING), ("timestamp", DESCENDING)], background=True)
        
        # Faults & Anomalies Collection
        logger.info("Creating indexes for: faults")
        await db.faults.create_index([("timestamp", DESCENDING)], background=True)
        await db.faults.create_index([("severity", ASCENDING), ("resolved_status", ASCENDING)], background=True)
        await db.faults.create_index([("location_id", ASCENDING)], background=True)
        
        # Transformers Collection
        logger.info("Creating indexes for: transformers")
        await db.transformers.create_index([("transformer_id", ASCENDING)], unique=True, background=True)
        await db.transformers.create_index([("health_status", ASCENDING)], background=True)
        await db.transformers.create_index([("last_maintenance", DESCENDING)], background=True)
        
        # Weather & Renewables Collection
        logger.info("Creating indexes for: weather_forecasts")
        await db.weather_forecasts.create_index([("timestamp", DESCENDING)], background=True)
        await db.weather_forecasts.create_index([("region", ASCENDING), ("timestamp", DESCENDING)], background=True)
        
        logger.info("MongoDB Index Optimization completed successfully!")
        
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(setup_database_indexes())
