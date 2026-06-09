import logging
from typing import List, Dict, Optional
from ..repositories.forecast_repository import ForecastRepository
from ..repositories.transformer_repository import TransformerRepository
from .prediction_service import TransformerPredictionService
from ..utils.helpers import utcnow
from ..core.config import settings
from ..core.grid_constants import SOURCE_SEED_DATA

logger = logging.getLogger("powercortex.services.transformer")

class TransformerService:
    """Business logic for transformer monitoring, predictive diagnostics, and data seeding."""
    
    def __init__(self, repository: TransformerRepository) -> None:
        self.repository = repository

    async def get_all_assets(self) -> List[Dict]:
        """Fetch all asset documents without creating demo records."""
        return await self.repository.get_all()

    async def get_asset_by_id(self, asset_id: str) -> Optional[Dict]:
        """Fetch details of a single asset by id or asset_id."""
        return await self.repository.get_by_id(asset_id)

    async def get_critical_assets(self) -> List[Dict]:
        """Fetch all assets currently in Critical status."""
        return await self.repository.get_by_status("Critical")

    async def get_warning_assets(self) -> List[Dict]:
        """Fetch all assets currently in Warning status."""
        return await self.repository.get_by_status("Warning")

    async def get_dashboard_summary(self) -> Dict[str, int]:
        """Retrieve total, healthy, warning, and critical counts."""
        return await self.repository.get_dashboard_summary()

    async def predict_and_save_telemetry(self, asset_id: str, telemetry: dict) -> Optional[dict]:
        """
        Receives new telemetry, executes RF model prediction, 
        calculates status, updates database, and returns the prediction result.
        """
        temp = telemetry.get("temperature", 70.0)
        volt = telemetry.get("voltage", 11.0)
        curr = telemetry.get("current", 300.0)
        oil = telemetry.get("oil_level", 85.0)
        load = telemetry.get("load_percentage", 70.0)
        
        predictions = TransformerPredictionService.run_inference(
            temperature=temp,
            voltage=volt,
            current=curr,
            oil_level=oil,
            load_percentage=load
        )

        # Apply data validation layer & consensus engine for Transformer Health
        try:
            from ..services.validation_service import ValidationService
            from ..core.database import get_database
            db = get_database()
            val_service = ValidationService(db)
            val_res = await val_service.validate_transformer_health(
                asset_id=asset_id,
                temp=temp,
                voltage=volt,
                current=curr,
                oil_level=oil,
                load_pct=load,
                primary_health=predictions["health_score"],
                failure_prob=predictions["failure_probability"]
            )
            
            # Downgrade if consensus disagrees
            consensus_data = val_service.calculate_consensus(
                prediction_type="transformer",
                inputs={"temp": temp, "load": load},
                primary_prediction="critical" if predictions["status"] == "Critical" else "normal"
            )
            agreement_score = consensus_data["agreement_score"]
            if predictions["status"] == "Critical" and agreement_score < 80.0:
                logger.info(f"Consensus agreement {agreement_score}% is below 80%. Downgrading transformer status from Critical to Warning.")
                predictions["status"] = "Warning"
        except Exception as val_err:
            logger.error(f"Error validating transformer health predictions: {val_err}")
        
        update_fields = {
            "temperature": temp,
            "voltage": volt,
            "current": curr,
            "oil_level": oil,
            "load_percentage": load,
            **predictions
        }
        
        result = await self.repository.update_telemetry(asset_id, update_fields)
        if result:
            result["_id"] = str(result["_id"])
        return result

    async def seed_initial_assets(self) -> None:
        """Seeds the database with the initial 8 assets matching the exact screenshot specs."""
        if not settings.ALLOW_DEMO_DATA:
            raise RuntimeError("Demo transformer seeding is disabled. Set ALLOW_DEMO_DATA=true to seed demo records.")
        logger.info("Seeding initial 8 assets...")
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
        
        now = utcnow()
        for doc in initial_data:
            doc["last_updated"] = now
            doc["data_source"] = SOURCE_SEED_DATA
            await self.repository.save(doc)
            
        logger.info("Successfully seeded 8 initial transformer assets in MongoDB.")
