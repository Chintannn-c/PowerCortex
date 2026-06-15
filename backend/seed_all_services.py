import asyncio
import os
import sys

# Add backend directory to system path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection, get_database
from app.repositories.fault_repository import FaultRepository
from app.repositories.transformer_repository import TransformerRepository
from app.repositories.theft_repository import TheftRepository
from app.services.fault_service import FaultDetectionService
from app.services.transformer_service import TransformerService
from app.services.theft_service import TheftDetectionService

async def main():
    # Force ALLOW_DEMO_DATA to True to permit seeding
    settings.ALLOW_DEMO_DATA = True
    
    print("Connecting to MongoDB...")
    await connect_to_mongo()
    db = get_database()
    
    # 1. Seed Faults
    print("Seeding faults...")
    fault_repo = FaultRepository(db)
    fault_service = FaultDetectionService(fault_repo)
    await fault_service.seed_initial_faults()
    
    # 2. Seed Transformer Assets
    print("Seeding transformer assets...")
    trans_repo = TransformerRepository(db)
    trans_service = TransformerService(trans_repo)
    await trans_service.seed_initial_assets()
    
    # 3. Seed Theft Alerts
    print("Seeding theft alerts...")
    theft_repo = TheftRepository(db)
    theft_service = TheftDetectionService(theft_repo)
    # Clear existing theft alerts to allow a clean slate
    await db.theft_alerts.delete_many({})
    await theft_service.seed_initial_theft_alerts()
    
    print("Closing MongoDB connection...")
    await close_mongo_connection()
    print("Seeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
