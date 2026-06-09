import os
import sys
import unittest
import asyncio
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient

# Add workspace backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.core.dependencies import get_current_user
from app.core.config import settings

# Override dependency to bypass auth and provide a mock _id
MOCK_USER_ID = "60d5ec4b9b1d8b2d888f4e12"
app.dependency_overrides[get_current_user] = lambda: {
    "_id": MOCK_USER_ID,
    "username": "admin",
    "email": "admin@guvnl.gov.in"
}

class TestAIAssistant(unittest.TestCase):
    
    def test_assistant_chat_endpoint(self):
        """Test POST /api/assistant/chat endpoint and verify DB persistence."""
        # Clear any existing test entries first using a dedicated test client/loop
        async def clear_old_entries():
            test_client = AsyncIOMotorClient(settings.MONGODB_URL)
            test_db = test_client[settings.DATABASE_NAME]
            await test_db.assistant_chats.delete_many({"user_id": MOCK_USER_ID})
            test_client.close()
        
        asyncio.run(clear_old_entries())
        
        with TestClient(app) as client:
            payload = {
                "message": "Predict tomorrow demand.",
                "history": []
            }
            response = client.post("/api/assistant/chat", json=payload)
            self.assertEqual(response.status_code, 200)
            
            res_data = response.json()
            self.assertTrue(res_data["success"])
            self.assertIn("reply", res_data)
            self.assertIn("confidence", res_data)
            
            # Verify DB storage using a dedicated test client/loop
            async def check_db():
                test_client = AsyncIOMotorClient(settings.MONGODB_URL)
                test_db = test_client[settings.DATABASE_NAME]
                entry = await test_db.assistant_chats.find_one({"user_id": MOCK_USER_ID})
                test_client.close()
                return entry

            entry = asyncio.run(check_db())
            self.assertIsNotNone(entry, "Chat entry was not persisted to the database!")
            self.assertEqual(entry["message"], "Predict tomorrow demand.")
            self.assertEqual(entry["reply"], res_data["reply"])
            self.assertEqual(entry["confidence"], res_data["confidence"])
            self.assertIn("timestamp", entry)
            
            print(f"\nVerified Database Persistence! Entry ID: {entry['_id']}")
            print(f"API Assistant Reply: {res_data['reply']}")

if __name__ == "__main__":
    unittest.main()
