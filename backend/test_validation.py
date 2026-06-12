import os
import sys
import unittest
import asyncio
from datetime import datetime
from fastapi.testclient import TestClient

# Add workspace backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.core.dependencies import get_current_user
from app.services.validation_service import ValidationService
from app.core.database import get_database

# Override dependency to bypass auth
app.dependency_overrides[get_current_user] = lambda: {"_id": "60d5ec4b9b1d8b2d888f4e12", "username": "admin", "email": "admin@guvnl.gov.in"}

class TestDataValidationLayer(unittest.TestCase):

    def setUp(self):
        self.client_ctx = TestClient(app)
        self.client = self.client_ctx.__enter__()
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

    def tearDown(self):
        if hasattr(self, "_clients_by_loop"):
            for client in self._clients_by_loop.values():
                client.close()
            self._clients_by_loop.clear()
        self.client_ctx.__exit__(None, None, None)

    def get_service(self):
        from motor.motor_asyncio import AsyncIOMotorClient
        from app.core.config import settings
        if not hasattr(self, "_clients_by_loop"):
            self._clients_by_loop = {}
        if self.loop not in self._clients_by_loop:
            self._clients_by_loop[self.loop] = AsyncIOMotorClient(settings.MONGODB_URL)
        db = self._clients_by_loop[self.loop][settings.DATABASE_NAME]
        return ValidationService(db)

    def test_load_validation(self):
        """Verify load forecast validations and rule checks."""
        val_service = self.get_service()
        # 1. Test normal load validation
        res = self.loop.run_until_complete(
            val_service.validate_load_forecast(
                predicted_demand=38000.0,
                temperature=25.0,
                hour=12,
                weekday=2
            )
        )
        self.assertTrue(res["validated"])
        self.assertGreaterEqual(res["confidence"], 90.0)
        self.assertIn("weather", res["validation_sources"])

        # 2. Test extreme temperature (AC load expected)
        res_hot = self.loop.run_until_complete(
            val_service.validate_load_forecast(
                predicted_demand=46000.0,
                temperature=42.0,
                hour=14,
                weekday=2
            )
        )
        self.assertIn("Extreme hot weather alert", res_hot["notes"])

        # 3. Test out of bounds demand
        res_out = self.loop.run_until_complete(
            val_service.validate_load_forecast(
                predicted_demand=60000.0,
                temperature=25.0,
                hour=12,
                weekday=2
            )
        )
        self.assertFalse(res_out["validated"])
        self.assertLess(res_out["confidence"], 90.0)
        self.assertIn("outside typical baseline bounds", res_out["notes"])

    def test_renewable_validation(self):
        """Verify Solar & Wind forecast validations."""
        val_service = self.get_service()
        # 1. Test solar nighttime or normal check
        res_night = self.loop.run_until_complete(
            val_service.validate_renewable_forecast(
                solar_forecast=500.0,
                wind_forecast=100.0,
                temp=22.0,
                humidity=60.0,
                wind_speed=5.0,
                cloud_cover=10.0
            )
        )
        self.assertIn("solar_forecast", res_night)
        
        # 2. Test Wind Turbine Cut-in/Cut-out Limit
        res_wind_low = self.loop.run_until_complete(
            val_service.validate_renewable_forecast(
                solar_forecast=0.0,
                wind_forecast=200.0,
                temp=25.0,
                humidity=50.0,
                wind_speed=2.0, # low wind speed (< 3m/s cut-in)
                cloud_cover=10.0
            )
        )
        self.assertEqual(res_wind_low["wind_forecast"], 0.0)
        self.assertFalse(res_wind_low["validated"])
        self.assertIn("low wind speed", res_wind_low["notes"].lower())

    def test_fault_validation(self):
        """Verify fault validation engineering rules and consensus."""
        val_service = self.get_service()
        # 1. Normal voltage, Sage predicted (conflict)
        res = self.loop.run_until_complete(
            val_service.validate_fault_detection(
                voltage=220.0,
                current=10.0,
                frequency=50.0,
                predicted_fault="Voltage Sag",
                dl_prob=92.0
            )
        )
        self.assertFalse(res["rule_validation"])
        self.assertIn("voltage sag predicted but voltage is normal", res["notes"].lower())

        # 2. Overload verification
        res_overload = self.loop.run_until_complete(
            val_service.validate_fault_detection(
                voltage=220.0,
                current=30.0, # > 25A
                frequency=50.0,
                predicted_fault="Overload",
                dl_prob=95.0
            )
        )
        self.assertTrue(res_overload["rule_validation"])
        self.assertGreaterEqual(res_overload["agreement_score"], 80.0)

    def test_theft_validation(self):
        """Verify theft validation checks."""
        val_service = self.get_service()
        # 1. Theft flagged, but consumption is above average (conflict)
        res = self.loop.run_until_complete(
            val_service.validate_theft_detection(
                consumer_id="CN-12345",
                consumption=150.0,
                avg_consumption=100.0,
                power_factor=0.95,
                predicted_risk=75.0
            )
        )
        self.assertFalse(res["validated"])
        self.assertIn("theft warning conflict", res["notes"].lower())

        # 2. Low power factor tampering flag
        res_pf = loop_pf = self.loop.run_until_complete(
            val_service.validate_theft_detection(
                consumer_id="CN-67890",
                consumption=40.0,
                avg_consumption=100.0,
                power_factor=0.65, # Low PF (< 0.75)
                predicted_risk=85.0
            )
        )
        self.assertTrue(res_pf["validated"])
        self.assertIn("power factor anomaly", res_pf["notes"].lower())

    def test_transformer_validation(self):
        """Verify transformer health validations."""
        val_service = self.get_service()
        # 1. Hot winding temperature conflict
        res = self.loop.run_until_complete(
            val_service.validate_transformer_health(
                asset_id="TR-X1",
                temp=98.0, # Critical (> 95)
                voltage=220.0,
                current=15.0,
                oil_level=85.0,
                load_pct=60.0,
                primary_health=85.0, # Predicted healthy
                failure_prob=10.0
            )
        )
        self.assertFalse(res["validated"])
        self.assertIn("severe thermal alert", res["notes"].lower())

    def test_api_validation_dashboard(self):
        """Test GET /api/validation/dashboard endpoint."""
        response = self.client.get("/api/validation/dashboard")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("prediction_confidence", data)
        self.assertIn("data_quality_score", data)
        self.assertIn("model_agreement_score", data)
        self.assertIn("api_status", data)
        self.assertIn("module_status", data)
        
        # Check individual statuses
        self.assertEqual(data["api_status"]["database"], "Connected")
        self.assertEqual(data["api_status"]["validation_engine"], "Active")
        self.assertTrue(data["module_status"]["load_forecasting"])
        print(f"Validation Dashboard Payload: {data}")

    def test_api_manual_check_endpoints(self):
        """Test POST manual check endpoints."""
        # 1. Load forecast validation endpoint
        response = self.client.post(
            "/api/validation/validate/load?predicted_demand=37500.0&temperature=28.5&hour=10&weekday=1"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("predicted_demand", data)
        self.assertIn("confidence", data)
        self.assertIn("validated", data)
        print(f"API Manual Load Validation: {data}")

        # 2. Renewable forecast validation endpoint
        response = self.client.post(
            "/api/validation/validate/renewable?solar_forecast=650.0&wind_forecast=220.0&temp=30.0&humidity=45.0&wind_speed=8.5&cloud_cover=15.0"
        )
        self.assertEqual(response.status_code, 200)
        data_renew = response.json()
        self.assertIn("solar_forecast", data_renew)
        self.assertIn("wind_forecast", data_renew)
        self.assertIn("validated", data_renew)
        print(f"API Manual Renewable Validation: {data_renew}")

if __name__ == "__main__":
    unittest.main()
