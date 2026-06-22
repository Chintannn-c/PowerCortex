import os
import sys
import unittest
from fastapi.testclient import TestClient

# Add backend dir to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.core.dependencies import get_current_user
from app.utils.model_loader import ModelLoader

# Bypass auth for testing
app.dependency_overrides[get_current_user] = lambda: {"_id": "60d5ec4b9b1d8b2d888f4e12", "username": "test_user", "email": "test@example.com"}

class TestTransformerHealthModule(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Ensure model is loaded (uses heuristic fallback if file is missing)
        ModelLoader.load_transformer_model()
        
        # Reset and seed collection synchronously using PyMongo
        # NOTE: settings.DATABASE_NAME is overridden to "powercortex_test"
        # by conftest.py, so this never touches the production database.
        from pymongo import MongoClient
        from app.core.config import settings
        from datetime import datetime, timezone
        
        mongo_client = MongoClient(settings.MONGODB_URL)
        db = mongo_client[settings.DATABASE_NAME]
        
        # Clear test transformers collection
        db.transformers.delete_many({})
        
        # Re-seed the 8 initial assets
        initial_data = [
            {
                "asset_id": "T-101",
                "name": "Transformer T-101",
                "type": "Distribution Transformer",
                "temperature": 67.0,
                "voltage": 11.2,
                "current": 320.0,
                "oil_level": 84.0,
                "load_percentage": 72.0,
                "health_score": 92.0,
                "risk_score": 8.0,
                "failure_probability": 3.0,
                "status": "Healthy"
            },
            {
                "asset_id": "T-104",
                "name": "Transformer T-104",
                "type": "Power Transformer",
                "temperature": 84.0,
                "voltage": 10.7,
                "current": 390.0,
                "oil_level": 72.0,
                "load_percentage": 85.0,
                "health_score": 64.0,
                "risk_score": 36.0,
                "failure_probability": 28.0,
                "status": "Warning"
            },
            {
                "asset_id": "T-108",
                "name": "Transformer T-108",
                "type": "Distribution Transformer",
                "temperature": 96.0,
                "voltage": 10.4,
                "current": 480.0,
                "oil_level": 48.0,
                "load_percentage": 95.0,
                "health_score": 38.0,
                "risk_score": 62.0,
                "failure_probability": 71.0,
                "status": "Critical"
            },
            {
                "asset_id": "F-22A",
                "name": "Feeder F-22A",
                "type": "11kV Feeder",
                "temperature": 68.0,
                "voltage": 11.1,
                "current": 280.0,
                "oil_level": 90.0,
                "load_percentage": 60.0,
                "health_score": 88.0,
                "risk_score": 12.0,
                "failure_probability": 8.0,
                "status": "Healthy"
            },
            {
                "asset_id": "F-15B",
                "name": "Feeder F-15B",
                "type": "33kV Feeder",
                "temperature": 79.0,
                "voltage": 10.8,
                "current": 350.0,
                "oil_level": 76.0,
                "load_percentage": 80.0,
                "health_score": 71.0,
                "risk_score": 29.0,
                "failure_probability": 21.0,
                "status": "Warning"
            },
            {
                "asset_id": "SS-04",
                "name": "Substation SS-04",
                "type": "66/11kV Substation",
                "temperature": 62.0,
                "voltage": 11.3,
                "current": 220.0,
                "oil_level": 95.0,
                "load_percentage": 52.0,
                "health_score": 95.0,
                "risk_score": 5.0,
                "failure_probability": 2.0,
                "status": "Healthy"
            },
            {
                "asset_id": "TL-22",
                "name": "Line TL-22",
                "type": "220kV Transmission",
                "temperature": 82.0,
                "voltage": 10.5,
                "current": 410.0,
                "oil_level": 80.0,
                "load_percentage": 88.0,
                "health_score": 56.0,
                "risk_score": 44.0,
                "failure_probability": 32.0,
                "status": "Warning"
            },
            {
                "asset_id": "T-112",
                "name": "Transformer T-112",
                "type": "Distribution Transformer",
                "temperature": 65.0,
                "voltage": 11.2,
                "current": 300.0,
                "oil_level": 88.0,
                "load_percentage": 66.0,
                "health_score": 82.0,
                "risk_score": 18.0,
                "failure_probability": 12.0,
                "status": "Healthy"
            }
        ]
        
        now = datetime.now(timezone.utc)
        for doc in initial_data:
            doc["last_updated"] = now
            db.transformers.insert_one(doc)
            
        mongo_client.close()

    def setUp(self):
        self.client_ctx = TestClient(app)
        self.client = self.client_ctx.__enter__()

    def tearDown(self):
        self.client_ctx.__exit__(None, None, None)

    @classmethod
    def tearDownClass(cls):
        """Clean up the test database collection after all tests."""
        from pymongo import MongoClient
        from app.core.config import settings
        mongo_client = MongoClient(settings.MONGODB_URL)
        db = mongo_client[settings.DATABASE_NAME]
        db.transformers.delete_many({})
        mongo_client.close()


    def test_predict_endpoint(self):
        print("Testing POST /api/transformers/predict...")
        payload = {
            "temperature": 67.0,
            "voltage": 11.2,
            "current": 320.0,
            "oil_level": 84.0,
            "load_percentage": 72.0
        }
        
        response = self.client.post("/api/transformers/predict", json=payload)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        print("Prediction result:", data)
        self.assertIn("health_score", data)
        self.assertIn("risk_score", data)
        self.assertIn("failure_probability", data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], "Healthy")

    def test_get_all_transformers(self):
        print("Testing GET /api/transformers...")
        response = self.client.get("/api/transformers")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(len(data["data"]), 8)
        print(f"Total transformers fetched: {len(data['data'])}")

    def test_dashboard_endpoint(self):
        print("Testing GET /api/transformers/dashboard...")
        response = self.client.get("/api/transformers/dashboard")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        print("Dashboard Summary:", data)
        self.assertIn("total", data)
        self.assertIn("healthy", data)
        self.assertIn("warning", data)
        self.assertIn("critical", data)
        self.assertEqual(data["total"], 8)
        self.assertEqual(data["healthy"], 4)
        self.assertEqual(data["warning"], 3)
        self.assertEqual(data["critical"], 1)

    def test_critical_endpoint(self):
        print("Testing GET /api/transformers/critical...")
        response = self.client.get("/api/transformers/critical")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["data"]), 1)
        self.assertEqual(data["data"][0]["asset_id"], "T-108")

    def test_warning_endpoint(self):
        print("Testing GET /api/transformers/warning...")
        response = self.client.get("/api/transformers/warning")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["data"]), 3)

    def test_telemetry_update(self):
        print("Testing POST /api/transformers/T-101/telemetry...")
        payload = {
            "temperature": 105.0,  # Very high temperature -> should lower health / change status
            "voltage": 11.2,
            "current": 320.0,
            "oil_level": 84.0,
            "load_percentage": 72.0
        }
        
        response = self.client.post("/api/transformers/T-101/telemetry", json=payload)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        print("Telemetry update response status:", data["status"], "Health:", data["health_score"])
        self.assertIn(data["status"], ["Warning", "Critical"])
        self.assertLess(data["health_score"], 80.0)

if __name__ == "__main__":
    unittest.main()
