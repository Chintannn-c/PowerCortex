import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.powercortex
    print("Database collections:", await db.list_collection_names())
    
    users = await db.users.find().to_list(10)
    print("\nRegistered Users:")
    for u in users:
        print(f"ID: {u['_id']}, Name: {u.get('full_name')}, Email: {u.get('email')}, IsActive: {u.get('is_active')}")
        
    forecasts = await db.forecasts.find().sort("created_at", -1).to_list(5)
    print("\nRecent Forecasts in DB:")
    for f in forecasts:
        print(f"Type: {f.get('forecast_type')}, Demand: {f.get('predicted_demand')}, CreatedAt: {f.get('created_at')}")

if __name__ == "__main__":
    asyncio.run(main())
