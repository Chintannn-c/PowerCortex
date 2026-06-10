import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
from ..repositories.fault_repository import FaultRepository
from ..utils.model_loader import ModelLoader
from ..utils.helpers import utcnow
from ..models.notification import NotificationCreate
from .notification_service import NotificationService
from ..core.config import settings
from ..core.config_loader import config
from ..core.grid_constants import SOURCE_SEED_DATA

logger = logging.getLogger("powercortex.services.fault")

class FaultDetectionService:
    """Service to handle Fault Detection ML predictions, heuristics, and notification triggers."""

    def __init__(self, repository: FaultRepository) -> None:
        self.repository = repository

    async def get_all_faults(self, limit: int = 100) -> List[Dict]:
        """Fetch all faults without creating demo records."""
        return await self.repository.get_all(limit)

    async def get_active_faults(self, limit: int = 100) -> List[Dict]:
        """Fetch active faults."""
        return await self.repository.get_active(limit)

    async def get_historical_faults(self, limit: int = 100) -> List[Dict]:
        """Fetch historical resolved faults."""
        return await self.repository.get_history(limit)

    async def get_fault_by_id(self, fault_id: str) -> Optional[Dict]:
        """Fetch details of a single fault by id or fault_id."""
        return await self.repository.get_by_id(fault_id)

    async def get_dashboard_summary(self) -> Dict[str, int]:
        """Fetch dashboard statistics counts."""
        return await self.repository.get_dashboard_summary()

    async def get_timeline_data(self) -> List[Dict]:
        """Fetch chronological timeline aggregates."""
        return await self.repository.get_timeline()

    async def predict_and_save_fault(self, voltage: float, current: float, frequency: float, asset_name: str = "Transmission Line TL-22A") -> Dict:
        """
        Runs the predictive pipeline:
        1. Executes ML inference.
        2. Applies electrical rules for extra fault classes (Frequency Deviation, Short Circuit, etc.).
        3. Computes severity and risk level from confidence.
        4. Saves the fault document.
        5. Automatically fires a push notification if Severity is Critical or High.
        """
        # 1. Run ML prediction
        pred_label, probability, prediction_source = ModelLoader.predict_fault(voltage, current, frequency)
        
        # Base classification from dataset labels
        # 0: Voltage Sag, 1: Overload, 2: Line Fault, 3: Voltage Swell
        label_mapping = {
            0: "Voltage Sag",
            1: "Overload",
            2: "Line Fault",
            3: "Voltage Swell"
        }
        fault_type = label_mapping.get(pred_label, "Line Fault")

        # 2. Heuristic rule-based overrides for additional faults
        freq_low = config.get("fault_detection.frequency_low_threshold", 48.8)
        freq_high = config.get("fault_detection.frequency_high_threshold", 51.2)
        sc_vol = config.get("fault_detection.short_circuit_voltage", 85.0)
        ef_cur = config.get("fault_detection.equipment_failure_current", 500.0)

        if frequency < freq_low or frequency > freq_high:
            fault_type = "Frequency Deviation"
            probability = max(probability, 92.0)
        elif voltage < sc_vol or (voltage < 160.0 and current > 350.0):
            fault_type = "Short Circuit"
            probability = max(probability, 96.5)
        elif "Transformer" in asset_name or "T-" in asset_name:
            if fault_type == "Overload":
                fault_type = "Transformer Fault"
        elif current > ef_cur or voltage < 50.0:
            fault_type = "Equipment Failure"
            probability = max(probability, 95.0)

        # 3. Calculate severity based on probability thresholds
        if probability >= 90.0:
            severity = "Critical"
        elif probability >= 75.0:
            severity = "High"
        elif probability >= 50.0:
            severity = "Medium"
        else:
            severity = "Low"

        # Apply multi-model consensus validation for Critical alerts
        if severity == "Critical":
            try:
                from ..services.validation_service import ValidationService
                from ..core.database import get_database
                db = get_database()
                val_service = ValidationService(db)
                val_res = await val_service.validate_fault_detection(
                    voltage=voltage,
                    current=current,
                    frequency=frequency,
                    predicted_fault=pred_label,
                    dl_prob=probability
                )
                agreement_score = val_res.get("agreement_score", 100.0)
                if agreement_score < 80.0:
                    logger.info(f"Consensus agreement {agreement_score}% is below 80%. Downgrading fault severity from Critical to High.")
                    severity = "High"
            except Exception as val_err:
                logger.error(f"Error executing fault validation consensus: {val_err}")


        # Generate unique human ID
        count = await self.repository._collection.count_documents({})
        fault_id = f"FLT-{count + 1:03d}"

        # 4. Construct fault document
        fault_doc = {
            "fault_id": fault_id,
            "fault_type": fault_type,
            "asset_name": asset_name,
            "severity": severity,
            "probability": probability,
            "prediction_source": prediction_source,
            "status": "Active",
            "voltage": voltage,
            "current": current,
            "frequency": frequency,
            "detected_at": utcnow()
        }

        # Save to database
        saved_doc = await self.repository.save(fault_doc)
        saved_doc["_id"] = str(saved_doc["_id"])

        # 5. Trigger push notification if Critical or High (probability >= 75)
        if severity in ["Critical", "High"]:
            await self.generate_alert(saved_doc)

        return saved_doc

    async def generate_alert(self, fault_doc: dict) -> None:
        """Helper to construct notification models and call NotificationService."""
        fault_id = fault_doc.get("fault_id", "FLT-001")
        fault_type = fault_doc.get("fault_type", "Voltage Sag")
        severity = fault_doc.get("severity", "Critical")
        asset_name = fault_doc.get("asset_name", "Transmission Line TL-22A")

        title = f"{severity} {fault_type} Detected"
        message = f"{asset_name} requires immediate attention."

        logger.info(f"Generating push alert for {fault_id} ({severity})")
        
        notification_data = NotificationCreate(
            title=title,
            message=message,
            type="fault",
            screen="FaultDetails",
            entity_id=fault_id
        )
        
        try:
            await NotificationService.create_and_send_notification(notification_data)
        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")

    async def seed_initial_faults(self) -> None:
        """Seed initial active and historical faults for demo purposes."""
        if not settings.ALLOW_DEMO_DATA:
            raise RuntimeError("Demo fault seeding is disabled. Set ALLOW_DEMO_DATA=true to seed demo records.")
        logger.info("Seeding initial faults dataset into MongoDB...")
        
        now = utcnow()
        
        initial_faults = [
            # Active Faults (8 items: 6 Critical, 1 High, 1 Medium)
            {
                "fault_id": "FLT-001",
                "fault_type": "Voltage Sag",
                "asset_name": "Transmission Line TL-22A",
                "severity": "Critical",
                "probability": 94.2,
                "status": "Active",
                "voltage": 185.0,
                "current": 450.0,
                "frequency": 49.1,
                "detected_at": now - timedelta(minutes=45)
            },
            {
                "fault_id": "FLT-002",
                "fault_type": "Overload",
                "asset_name": "Transformer T-104",
                "severity": "Critical",
                "probability": 91.8,
                "status": "Active",
                "voltage": 220.0,
                "current": 490.0,
                "frequency": 50.0,
                "detected_at": now - timedelta(hours=2)
            },
            {
                "fault_id": "FLT-003",
                "fault_type": "Short Circuit",
                "asset_name": "Feeder F-22A",
                "severity": "Critical",
                "probability": 96.5,
                "status": "Active",
                "voltage": 85.0,
                "current": 420.0,
                "frequency": 49.8,
                "detected_at": now - timedelta(hours=3)
            },
            {
                "fault_id": "FLT-004",
                "fault_type": "Equipment Failure",
                "asset_name": "Substation SS-04",
                "severity": "Critical",
                "probability": 95.0,
                "status": "Active",
                "voltage": 210.0,
                "current": 520.0,
                "frequency": 50.1,
                "detected_at": now - timedelta(hours=4)
            },
            {
                "fault_id": "FLT-005",
                "fault_type": "Transformer Fault",
                "asset_name": "Transformer T-112",
                "severity": "Critical",
                "probability": 92.5,
                "status": "Active",
                "voltage": 195.0,
                "current": 460.0,
                "frequency": 49.9,
                "detected_at": now - timedelta(hours=5)
            },
            {
                "fault_id": "FLT-006",
                "fault_type": "Frequency Deviation",
                "asset_name": "Transmission Line TL-12",
                "severity": "Critical",
                "probability": 93.8,
                "status": "Active",
                "voltage": 218.0,
                "current": 25.0,
                "frequency": 48.2,
                "detected_at": now - timedelta(hours=5, minutes=30)
            },
            {
                "fault_id": "FLT-007",
                "fault_type": "Line Fault",
                "asset_name": "Feeder F-15B",
                "severity": "High",
                "probability": 87.5,
                "status": "Active",
                "voltage": 175.0,
                "current": 37.4,
                "frequency": 48.8,
                "detected_at": now - timedelta(hours=6)
            },
            {
                "fault_id": "FLT-008",
                "fault_type": "Voltage Swell",
                "asset_name": "Substation SS-02",
                "severity": "Medium",
                "probability": 82.3,
                "status": "Active",
                "voltage": 258.0,
                "current": 13.9,
                "frequency": 50.5,
                "detected_at": now - timedelta(hours=7)
            },
            # Historical Resolved Faults (4 items)
            {
                "fault_id": "FLT-009",
                "fault_type": "Voltage Sag",
                "asset_name": "Feeder F-22A",
                "severity": "High",
                "probability": 76.5,
                "status": "Resolved",
                "voltage": 192.0,
                "current": 18.0,
                "frequency": 49.6,
                "detected_at": now - timedelta(days=2, hours=1)
            },
            {
                "fault_id": "FLT-010",
                "fault_type": "Overload",
                "asset_name": "Transformer T-112",
                "severity": "Medium",
                "probability": 65.2,
                "status": "Resolved",
                "voltage": 215.0,
                "current": 320.0,
                "frequency": 49.9,
                "detected_at": now - timedelta(days=2, hours=3)
            },
            {
                "fault_id": "FLT-011",
                "fault_type": "Line Fault",
                "asset_name": "Line TL-22",
                "severity": "Critical",
                "probability": 93.1,
                "status": "Resolved",
                "voltage": 172.0,
                "current": 380.0,
                "frequency": 48.9,
                "detected_at": now - timedelta(days=1, hours=2)
            },
            {
                "fault_id": "FLT-012",
                "fault_type": "Voltage Swell",
                "asset_name": "Feeder F-15B",
                "severity": "Low",
                "probability": 48.0,
                "status": "Resolved",
                "voltage": 252.0,
                "current": 12.0,
                "frequency": 50.3,
                "detected_at": now - timedelta(days=1, hours=5)
            }
        ]

        for doc in initial_faults:
            doc["data_source"] = SOURCE_SEED_DATA
            await self.repository.save(doc)
            
        logger.info(f"Successfully seeded {len(initial_faults)} initial faults in MongoDB.")
