import os
import sys
import unittest
from fastapi.testclient import TestClient

# Add workspace backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.core.dependencies import get_current_user
from app.utils.model_loader import ModelLoader

# Override dependency to bypass auth
app.dependency_overrides[get_current_user] = lambda: {"_id": "60d5ec4b9b1d8b2d888f4e12", "username": "admin", "email": "admin@guvnl.gov.in"}

class TestTheftDetection(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Force model loading if not already loaded
        ModelLoader.load_theft_model()

    def setUp(self):
        # Reset and seed collection synchronously using PyMongo to avoid async loop conflicts
        from pymongo import MongoClient
        from app.core.config import settings
        from datetime import datetime, timedelta, timezone

        mongo_client = MongoClient(settings.MONGODB_URL)
        db = mongo_client[settings.DATABASE_NAME]

        # Clear theft_alerts collection
        db.theft_alerts.delete_many({})

        now = datetime.now(timezone.utc)
        # Seed CN-88029
        db.theft_alerts.insert_one({
            "consumer_id": "CN-88029",
            "consumer_name": "Consumer A",
            "sector": "Sector 4",
            "city": settings.DEFAULT_CITY,
            "current_consumption": 420.0,
            "avg_consumption": 1180.0,
            "power_factor": 0.72,
            "monthly_usage": [1250, 1190, 1230, 1175, 420],
            "theft_probability": 91.2,
            "risk_level": "High Risk",
            "deviation_percentage": -64.6,
            "is_suspicious": True,
            "status": "Active",
            "created_at": now - timedelta(hours=1)
        })
        mongo_client.close()

    def test_model_loading(self):
        """Verify the theft detection model and scaler are loaded properly."""
        self.assertIsNotNone(ModelLoader._theft_model, "Isolation Forest model should not be None")
        self.assertIsNotNone(ModelLoader._theft_scaler, "StandardScaler should not be None")

    def test_model_inference(self):
        """Test Isolation Forest inference method with various inputs."""
        # Test normal consumption
        prob, is_suspicious, deviation, source = ModelLoader.predict_theft(1000.0, 1000.0, 0.95)
        self.assertFalse(is_suspicious)
        self.assertTrue(0.0 <= prob < 50.0)
        self.assertEqual(deviation, 0.0)
        print(f"Normal consumption prediction: Prob={prob}%, Suspicious={is_suspicious}, Deviation={deviation}%")

        # Test anomaly consumption (large drop in consumption)
        prob, is_suspicious, deviation, source = ModelLoader.predict_theft(100.0, 1200.0, 0.50)
        self.assertTrue(is_suspicious)
        self.assertTrue(50.0 <= prob <= 100.0)
        self.assertTrue(deviation < -50.0)
        print(f"Anomalous consumption prediction: Prob={prob}%, Suspicious={is_suspicious}, Deviation={deviation}%")

    def test_api_predict_endpoint(self):
        """Test POST /api/theft/predict endpoint."""
        with TestClient(app) as client:
            payload = {
                "consumer_id": "CN-TEST-999",
                "current_consumption": 450.0,
                "avg_consumption": 1200.0,
                "power_factor": 0.70
            }
            response = client.post("/api/theft/predict", json=payload)
            self.assertEqual(response.status_code, 200)
            
            res_data = response.json()
            self.assertTrue(res_data["success"])
            data = res_data["data"]
            self.assertEqual(data["consumer_id"], "CN-TEST-999")
            self.assertIn("theft_probability", data)
            self.assertIn("risk_level", data)
            self.assertIn("deviation_percentage", data)
            print(f"API Predict Response: {res_data}")

    def test_api_get_endpoints(self):
        """Test GET endpoints for theft detection."""
        with TestClient(app) as client:
            # Get dashboard metrics
            response = client.get("/api/theft/dashboard")
            self.assertEqual(response.status_code, 200)
            dashboard = response.json()
            self.assertIn("suspicious_count", dashboard)
            self.assertIn("high_risk_count", dashboard)
            self.assertIn("resolved_count", dashboard)
            self.assertIn("average_probability", dashboard)
            print(f"API Dashboard Stats: {dashboard}")

            # Get suspicious consumers list
            response = client.get("/api/theft/suspicious")
            self.assertEqual(response.status_code, 200)
            suspicious = response.json()
            self.assertTrue(isinstance(suspicious, list))
            if len(suspicious) > 0:
                item = suspicious[0]
                self.assertIn("consumer_id", item)
                self.assertIn("risk_level", item)
                self.assertIn("theft_probability", item)
            print(f"API Suspicious Count: {len(suspicious)}")

            # Get distribution stats
            response = client.get("/api/theft/distribution")
            self.assertEqual(response.status_code, 200)
            distribution = response.json()
            self.assertTrue(isinstance(distribution, list))
            print(f"API Risk Distribution: {distribution}")

            # Test detailed investigation and trend for specific consumer from seeded data (CN-88029)
            response = client.get("/api/theft/consumer/CN-88029")
            self.assertEqual(response.status_code, 200)
            details = response.json()
            self.assertEqual(details["consumer_id"], "CN-88029")
            self.assertIn("ai_explanation", details)
            self.assertIn("monthly_usage", details)
            print(f"API Consumer Details: {details}")

            response = client.get("/api/theft/trend/CN-88029")
            self.assertEqual(response.status_code, 200)
            trend = response.json()
            self.assertTrue(isinstance(trend, list))
            self.assertTrue(len(trend) > 0)
            self.assertIn("month", trend[0])
            self.assertIn("actual", trend[0])
            self.assertIn("expected", trend[0])
            print(f"API Consumption Trend: {trend}")

if __name__ == "__main__":
    unittest.main()
