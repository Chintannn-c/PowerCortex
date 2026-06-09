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
app.dependency_overrides[get_current_user] = lambda: {
    "_id": "60d5ec4b9b1d8b2d888f4e12",
    "username": "admin",
    "email": "admin@guvnl.gov.in"
}

class TestSystemHealth(unittest.TestCase):
    
    def test_model_prediction(self):
        """Test Keras prediction or heuristic fallback from ModelLoader."""
        # Warmup and load
        ModelLoader.load_system_health_model()
        
        # Test case 1: healthy parameters
        health_score, failure_prob = ModelLoader.predict_system_health(
            cpu_usage=15.0,
            memory_usage=30.0,
            network_latency=10.0,
            db_connected=1.0,
            api_latency=20.0
        )
        self.assertGreaterEqual(health_score, 80.0)
        self.assertLessEqual(failure_prob, 30.0)
        
        # Test case 2: critical parameters (db disconnected)
        health_score_crit, failure_prob_crit = ModelLoader.predict_system_health(
            cpu_usage=15.0,
            memory_usage=30.0,
            network_latency=0.0,
            db_connected=0.0,
            api_latency=20.0
        )
        self.assertLess(health_score_crit, 70.0)
        self.assertGreater(failure_prob_crit, 30.0)
        
    def test_health_check_endpoint(self):
        """Test GET /api/system/health endpoint."""
        with TestClient(app) as client:
            response = client.get("/api/system/health")
            self.assertEqual(response.status_code, 200)
            
            res_data = response.json()
            self.assertTrue(res_data["success"])
            self.assertIn("overall_status", res_data)
            self.assertIn("overall_health_score", res_data)
            self.assertIn("failure_probability", res_data)
            self.assertIn("services", res_data)
            
            services = res_data["services"]
            self.assertIn("backend", services)
            self.assertIn("database", services)
            self.assertIn("ai_engine", services)
            self.assertIn("ml_pipeline", services)
            
            print(f"System Health Score (DL Evaluated): {res_data['overall_health_score']}%")
            print(f"Predicted Failure Probability: {res_data['failure_probability']}%")
            print(f"FastAPI CPU usage: {services['backend']['cpu_usage']}%")

if __name__ == "__main__":
    unittest.main()
