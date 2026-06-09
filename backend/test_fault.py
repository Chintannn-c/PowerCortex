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
app.dependency_overrides[get_current_user] = lambda: {"username": "admin", "email": "admin@guvnl.gov.in"}

class TestFaultDetection(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Force model loading if not already loaded
        ModelLoader.load_fault_model()

    def test_model_loading(self):
        """Verify the model and scaler are loaded properly."""
        self.assertIsNotNone(ModelLoader._fault_model, "Keras model should not be None")
        self.assertIsNotNone(ModelLoader._fault_scaler, "StandardScaler should not be None")

    def test_model_inference(self):
        """Test Keras inference method with various inputs."""
        # 0: Voltage Sag, 1: Overload, 2: Line Fault, 3: Voltage Swell
        
        # Test Voltage Sag prediction
        label, prob = ModelLoader.predict_fault(180.0, 15.0, 50.0)
        self.assertIn(label, [0, 1, 2, 3])
        self.assertTrue(0.0 <= prob <= 100.0)
        print(f"Voltage Sag test prediction: Label={label}, Probability={prob:.2f}%")

        # Test Overload prediction (Amperes scaled dynamically by /10)
        label, prob = ModelLoader.predict_fault(220.0, 480.0, 50.0)
        self.assertIn(label, [0, 1, 2, 3])
        self.assertTrue(0.0 <= prob <= 100.0)
        print(f"Overload test prediction: Label={label}, Probability={prob:.2f}%")

        # Test Swell prediction
        label, prob = ModelLoader.predict_fault(260.0, 10.0, 50.0)
        self.assertIn(label, [0, 1, 2, 3])
        self.assertTrue(0.0 <= prob <= 100.0)
        print(f"Voltage Swell test prediction: Label={label}, Probability={prob:.2f}%")

    def test_api_predict_endpoint(self):
        """Test POST /api/faults/predict endpoint."""
        with TestClient(app) as client:
            payload = {
                "voltage": 185.0,
                "current": 450.0,
                "frequency": 49.2,
                "asset_name": "Transmission Line TL-33"
            }
            response = client.post("/api/faults/predict", json=payload)
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn("fault_type", data)
            self.assertIn("severity", data)
            self.assertIn("probability", data)
            self.assertEqual(data["status"], "Active")
            print(f"API Predict Response: {data}")

    def test_api_get_endpoints(self):
        """Test GET endpoints for faults."""
        with TestClient(app) as client:
            # Get dashboard metrics
            response = client.get("/api/faults/dashboard")
            self.assertEqual(response.status_code, 200)
            dashboard = response.json()
            self.assertIn("active_faults", dashboard)
            self.assertIn("critical", dashboard)
            print(f"API Dashboard Stats: {dashboard}")

            # Get active faults list
            response = client.get("/api/faults/active")
            self.assertEqual(response.status_code, 200)
            res_data = response.json()
            self.assertTrue(res_data["success"])
            self.assertTrue(isinstance(res_data["data"], list))
            print(f"API Active Faults Count: {len(res_data['data'])}")

            # Get timeline points
            response = client.get("/api/faults/timeline")
            self.assertEqual(response.status_code, 200)
            self.assertTrue(isinstance(response.json(), list))

            # Get anomalies widget data
            response = client.get("/api/faults/anomalies")
            self.assertEqual(response.status_code, 200)
            anomalies_data = response.json()
            self.assertIn("active_faults", anomalies_data)
            self.assertTrue(isinstance(anomalies_data["faults"], list))

if __name__ == "__main__":
    unittest.main()
