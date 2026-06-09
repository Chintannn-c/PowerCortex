import os
import sys
import unittest
from fastapi.testclient import TestClient
from datetime import datetime

# Add workspace backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.core.dependencies import get_current_user
from app.ml.renewable_predictor import RenewablePredictor

# Override dependency to bypass auth
app.dependency_overrides[get_current_user] = lambda: {
    "_id": "60d5ec4b9b1d8b2d888f4e12",
    "username": "admin",
    "email": "admin@guvnl.gov.in"
}

class TestRenewableForecast(unittest.TestCase):
    
    def test_model_prediction(self):
        """Test the ML inference outputs for solar and wind generation."""
        solar, wind = RenewablePredictor.predict_renewables(
            temp=34.0,
            humidity=65.0,
            wind_speed=13.0,
            cloud_cover=50.0
        )
        # Test values should reflect realistic ranges (e.g. ~742 MW and ~312 MW)
        self.assertGreater(solar, 400.0)
        self.assertLess(solar, 1000.0)
        self.assertGreater(wind, 150.0)
        self.assertLess(wind, 500.0)
        print(f"Verified prediction: Solar={solar} MW, Wind={wind} MW")

    def test_current_forecast_endpoint(self):
        """Test GET /api/renewables/current endpoint."""
        with TestClient(app) as client:
            response = client.get("/api/renewables/current")
            self.assertEqual(response.status_code, 200)
            res_data = response.json()
            self.assertIn("solar_generation", res_data)
            self.assertIn("wind_generation", res_data)
            self.assertIn("renewable_total", res_data)
            self.assertIn("timestamp", res_data)
            print(f"GET /current: Solar={res_data['solar_generation']} MW, Wind={res_data['wind_generation']} MW")

    def test_predict_endpoint(self):
        """Test POST /api/renewables/predict endpoint."""
        with TestClient(app) as client:
            req_payload = {
                "temperature": 34.0,
                "humidity": 65.0,
                "wind_speed": 13.0,
                "cloud_cover": 50.0
            }
            response = client.post("/api/renewables/predict", json=req_payload)
            self.assertEqual(response.status_code, 200)
            res_data = response.json()
            self.assertIn("solar_generation", res_data)
            self.assertIn("wind_generation", res_data)
            self.assertIn("renewable_total", res_data)
            print(f"POST /predict: Solar={res_data['solar_generation']} MW, Wind={res_data['wind_generation']} MW")

    def test_history_endpoint(self):
        """Test GET /api/renewables/history endpoint."""
        with TestClient(app) as client:
            response = client.get("/api/renewables/history?limit=5")
            self.assertEqual(response.status_code, 200)
            res_data = response.json()
            self.assertTrue(isinstance(res_data, dict))
            self.assertEqual(res_data.get("success"), True)
            self.assertTrue(isinstance(res_data.get("data"), list))
            print(f"GET /history: Returned {len(res_data.get('data', []))} records.")

if __name__ == "__main__":
    unittest.main()