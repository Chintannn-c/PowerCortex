import asyncio
import sys
import os

# Adjust path so we can import from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import connect_to_mongo, close_mongo_connection, get_database
from app.services.assistant_service import AssistantService

async def run_tests():
    print("--- Starting Smart Search Service Test ---")
    await connect_to_mongo()
    db = get_database()
    
    service = AssistantService(db)
    
    test_queries = [
        "what is the load on the grid right now?",
        "weather in Ahmedabad",
        "open the settings panel",
        "critical diagnostics status",
        "any suspicious theft alerts?",
        "show me forecasting screen",
        "random search query text"
    ]
    
    for q in test_queries:
        print(f"\nQuery: '{q}'")
        res = await service.parse_smart_search(q)
        print(f"Result: {res}")
        
    await close_mongo_connection()
    print("\n--- Smart Search Service Test Completed ---")

if __name__ == "__main__":
    asyncio.run(run_tests())
