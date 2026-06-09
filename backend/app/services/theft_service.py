from ..core.config import settings
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
from ..repositories.theft_repository import TheftRepository
from ..utils.model_loader import ModelLoader
from ..utils.helpers import utcnow
from ..models.notification import NotificationCreate
from .notification_service import NotificationService
from ..core.config import settings
from ..core.exceptions import IncompleteOperationalDataError
from ..core.config_loader import config
from ..core.grid_constants import SOURCE_SEED_DATA

logger = logging.getLogger("powercortex.services.theft")

class TheftDetectionService:
    """Service to handle Power Theft predictions, risk scoring, notification triggers, and DB queries."""

    def __init__(self, repository: TheftRepository) -> None:
        self.repository = repository

    async def get_all_suspicious(self, limit: int = 100) -> List[Dict]:
        """Fetch all active suspicious alerts without creating demo records."""
        return await self.repository.get_all_suspicious(limit)

    async def get_dashboard_summary(self) -> Dict[str, any]:
        """Fetch summary counts for dashboard widgets."""
        return await self.repository.get_dashboard_summary()

    async def get_risk_distribution(self) -> List[Dict]:
        """Fetch risk distribution list for Syncfusion pie chart representation."""
        dist = await self.repository.get_risk_distribution()
        return [
            {"name": "High Risk", "value": dist["High Risk"]},
            {"name": "Medium Risk", "value": dist["Medium Risk"]},
            {"name": "Low Risk", "value": dist["Low Risk"]},
            {"name": "Normal", "value": dist["Normal"]},
        ]

    async def get_consumer_investigation(self, consumer_id: str) -> Optional[Dict]:
        """Fetch full profile data, including monthly consumption history and AI explanation."""
        alert = await self.repository.get_by_consumer_id(consumer_id)
        if not alert:
            return None

        required_fields = [
            "consumer_name",
            "sector",
            "city",
            "current_consumption",
            "avg_consumption",
            "power_factor",
            "monthly_usage",
            "deviation_percentage",
            "theft_probability",
            "risk_level",
            "is_suspicious",
        ]
        missing = [field for field in required_fields if field not in alert or alert.get(field) is None]
        if missing:
            raise IncompleteOperationalDataError(
                f"Consumer profile '{consumer_id}' is missing required fields: {', '.join(missing)}"
            )

        current = alert["current_consumption"]
        avg = alert["avg_consumption"]
        pf = alert["power_factor"]
        monthly_usage = alert["monthly_usage"]
        
        # Calculate expected trend (expected should be close to average consumption)
        # AI Explanation notes
        deviation = alert["deviation_percentage"]
        ai_explanation = (
            f"Consumer {consumer_id} shows a severe anomaly in current monthly consumption. "
            f"The current consumption ({current} kWh) dropped by {abs(deviation):.1f}% relative "
            f"to their 12-month average consumption ({avg} kWh). The power factor of {pf} is "
            f"sub-optimal, indicating possible meter tampering or shunt insertion."
        )
        
        return {
            "consumer_id": alert["consumer_id"],
            "consumer_name": alert["consumer_name"],
            "sector": alert["sector"],
            "city": alert["city"],
            "current_consumption": current,
            "avg_consumption": avg,
            "power_factor": pf,
            "monthly_usage": monthly_usage,
            "theft_probability": alert["theft_probability"],
            "risk_level": alert["risk_level"],
            "deviation_percentage": deviation,
            "is_suspicious": alert["is_suspicious"],
            "ai_explanation": ai_explanation,
            "investigation_notes": alert.get("investigation_notes", "No investigation notes recorded.")
        }

    async def predict_and_save_theft(
        self,
        consumer_id: str,
        current_consumption: Optional[float] = None,
        avg_consumption: Optional[float] = None,
        power_factor: Optional[float] = None,
        consumer_name: str = "Unassigned",
        sector: str = "Sector 4",
        city: str = "",
        monthly_usage: Optional[List[float]] = None
    ) -> Dict:
        """
        Runs the theft detection prediction:
        1. Loads defaults if parameters are omitted.
        2. Executes Isolation Forest inference.
        3. Assigns risk level.
        4. Triggers push notification if theft probability > 85%.
        5. Persists the alert to MongoDB.
        """
        missing_inputs = [
            name for name, value in {
                "current_consumption": current_consumption,
                "avg_consumption": avg_consumption,
                "power_factor": power_factor,
            }.items()
            if value is None
        ]
        if missing_inputs:
            raise ValueError(f"Missing required theft telemetry: {', '.join(missing_inputs)}")
        if monthly_usage is None:
            monthly_usage = [float(current_consumption)]

        # 1. Run Isolation Forest ML prediction
        prob, is_suspicious, deviation, prediction_source = ModelLoader.predict_theft(
            current_consumption, avg_consumption, power_factor
        )

        # 2. Risk classification threshold logic
        high = config.get("theft_detection.high_risk_threshold", 90.0)
        medium = config.get("theft_detection.medium_risk_threshold", 70.0)
        low = config.get("theft_detection.low_risk_threshold", 50.0)

        if prob >= high:
            risk_level = "High Risk"
        elif prob >= medium:
            risk_level = "Medium Risk"
        elif prob >= low:
            risk_level = "Low Risk"
        else:
            risk_level = "Normal"

        # Apply multi-model consensus validation for High Risk alerts
        try:
            from ..services.validation_service import ValidationService
            from ..core.database import get_database
            db = get_database()
            val_service = ValidationService(db)
            val_res = await val_service.validate_theft_detection(
                consumer_id=consumer_id,
                consumption=current_consumption,
                avg_consumption=avg_consumption,
                power_factor=power_factor,
                predicted_risk=prob
            )
            consensus_data = val_service.calculate_consensus(
                prediction_type="theft",
                inputs={"deviation": deviation, "power_factor": power_factor},
                primary_prediction="suspicious" if prob > 50.0 else "normal"
            )
            agreement_score = consensus_data["agreement_score"]
            if risk_level == "High Risk" and agreement_score < 80.0:
                logger.info(f"Consensus agreement {agreement_score}% is below 80%. Downgrading theft alert from High Risk to Medium Risk.")
                risk_level = "Medium Risk"
                prob = min(prob, 84.9)
        except Exception as val_err:
            logger.error(f"Error executing theft validation: {val_err}")

        # 3. Construct the alert document
        alert_doc = {
            "consumer_id": consumer_id,
            "consumer_name": consumer_name,
            "sector": sector,
            "city": city,
            "current_consumption": current_consumption,
            "avg_consumption": avg_consumption,
            "power_factor": power_factor,
            "monthly_usage": monthly_usage,
            "theft_probability": prob,
            "risk_level": risk_level,
            "deviation_percentage": deviation,
            "is_suspicious": is_suspicious,
            "prediction_source": prediction_source,
            "status": "Active",
            "created_at": utcnow()
        }

        # Save to database
        saved_doc = await self.repository.save_alert(alert_doc)
        
        # 4. Trigger push notification if probability > notification threshold
        notify_thresh = config.get("theft_detection.notification_threshold", 85.0)
        if prob >= notify_thresh:
            await self.generate_push_notification(saved_doc)

        return saved_doc

    async def generate_push_notification(self, alert_doc: dict) -> None:
        """Create database notification and trigger FCM push simulation."""
        consumer_id = alert_doc["consumer_id"]
        prob = alert_doc["theft_probability"]
        
        title = "High Theft Risk Detected"
        message = f"Consumer {consumer_id} has {prob}% theft probability"
        
        logger.info(f"Triggering push notification for theft alert {consumer_id} ({prob}%)")
        
        notification_data = NotificationCreate(
            title=title,
            message=message,
            type="theft",
            screen="TheftDetails",
            entity_id=consumer_id
        )
        
        try:
            await NotificationService.create_and_send_notification(notification_data)
        except Exception as e:
            logger.error(f"Failed to dispatch FCM push notification: {e}")

    async def seed_initial_theft_alerts(self) -> None:
        """Seed initial suspicious and resolved cases into theft_alerts collection."""
        if not settings.ALLOW_DEMO_DATA:
            raise RuntimeError("Demo theft seeding is disabled. Set ALLOW_DEMO_DATA=true to seed demo records.")
        logger.info("Seeding theft alerts collection...")
        
        now = utcnow()
        
        # 12 Active Suspicious Consumers
        # Total sum of probabilities = 940.8 (resulting in exactly 78.4% average probability)
        active_suspicious = [
            {
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
            },
            {
                "consumer_id": "CN-45210",
                "consumer_name": "Consumer B",
                "sector": "Sector 12",
                "city": "Surat",
                "current_consumption": 490.0,
                "avg_consumption": 1022.0,
                "power_factor": 0.75,
                "monthly_usage": [980, 1020, 990, 1050, 490],
                "theft_probability": 84.5,
                "risk_level": "High Risk",
                "deviation_percentage": -52.1,
                "is_suspicious": True,
                "status": "Active",
                "created_at": now - timedelta(hours=3)
            },
            {
                "consumer_id": "CN-71034",
                "consumer_name": "Consumer C",
                "sector": "Sector 8",
                "city": "Vadodara",
                "current_consumption": 530.0,
                "avg_consumption": 860.0,
                "power_factor": 0.78,
                "monthly_usage": [850, 890, 860, 880, 530],
                "theft_probability": 72.8,
                "risk_level": "Medium Risk",
                "deviation_percentage": -38.4,
                "is_suspicious": True,
                "status": "Active",
                "created_at": now - timedelta(hours=5)
            },
            {
                "consumer_id": "CN-93821",
                "consumer_name": "Consumer D",
                "sector": "Sector 2",
                "city": "Rajkot",
                "current_consumption": 520.0,
                "avg_consumption": 730.0,
                "power_factor": 0.81,
                "monthly_usage": [720, 750, 710, 740, 520],
                "theft_probability": 65.3,
                "risk_level": "Medium Risk",
                "deviation_percentage": -28.9,
                "is_suspicious": True,
                "status": "Active",
                "created_at": now - timedelta(hours=8)
            },
            {
                "consumer_id": "CN-12405",
                "consumer_name": "Consumer E",
                "sector": "Sector 6",
                "city": "Gandhinagar",
                "current_consumption": 500.0,
                "avg_consumption": 645.0,
                "power_factor": 0.83,
                "monthly_usage": [640, 670, 630, 660, 500],
                "theft_probability": 58.1,
                "risk_level": "Low Risk",
                "deviation_percentage": -22.5,
                "is_suspicious": True,
                "status": "Active",
                "created_at": now - timedelta(hours=10)
            },
            {
                "consumer_id": "CN-30982",
                "consumer_name": "Consumer F",
                "sector": "Sector 5",
                "city": settings.DEFAULT_CITY,
                "current_consumption": 350.0,
                "avg_consumption": 1100.0,
                "power_factor": 0.69,
                "monthly_usage": [1150, 1080, 1120, 1100, 350],
                "theft_probability": 93.5,
                "risk_level": "High Risk",
                "deviation_percentage": -68.2,
                "is_suspicious": True,
                "status": "Active",
                "created_at": now - timedelta(hours=12)
            },
            {
                "consumer_id": "CN-52901",
                "consumer_name": "Consumer G",
                "sector": "Sector 3",
                "city": "Surat",
                "current_consumption": 440.0,
                "avg_consumption": 1128.0,
                "power_factor": 0.71,
                "monthly_usage": [1100, 1150, 1130, 1110, 440],
                "theft_probability": 90.2,
                "risk_level": "High Risk",
                "deviation_percentage": -61.0,
                "is_suspicious": True,
                "status": "Active",
                "created_at": now - timedelta(hours=14)
            },
            {
                "consumer_id": "CN-66023",
                "consumer_name": "Consumer H",
                "sector": "Sector 1",
                "city": "Vadodara",
                "current_consumption": 460.0,
                "avg_consumption": 800.0,
                "power_factor": 0.76,
                "monthly_usage": [820, 810, 790, 800, 460],
                "theft_probability": 82.5,
                "risk_level": "Medium Risk",
                "deviation_percentage": -42.5,
                "is_suspicious": True,
                "status": "Active",
                "created_at": now - timedelta(hours=16)
            },
            {
                "consumer_id": "CN-10294",
                "consumer_name": "Consumer I",
                "sector": "Sector 9",
                "city": "Rajkot",
                "current_consumption": 490.0,
                "avg_consumption": 805.0,
                "power_factor": 0.77,
                "monthly_usage": [810, 790, 820, 800, 490],
                "theft_probability": 81.0,
                "risk_level": "Medium Risk",
                "deviation_percentage": -39.1,
                "is_suspicious": True,
                "status": "Active",
                "created_at": now - timedelta(hours=18)
            },
            {
                "consumer_id": "CN-22904",
                "consumer_name": "Consumer J",
                "sector": "Sector 2",
                "city": settings.DEFAULT_CITY,
                "current_consumption": 550.0,
                "avg_consumption": 848.0,
                "power_factor": 0.78,
                "monthly_usage": [860, 830, 850, 840, 550],
                "theft_probability": 78.6,
                "risk_level": "Medium Risk",
                "deviation_percentage": -35.2,
                "is_suspicious": True,
                "status": "Active",
                "created_at": now - timedelta(hours=20)
            },
            {
                "consumer_id": "CN-40192",
                "consumer_name": "Consumer K",
                "sector": "Sector 15",
                "city": "Surat",
                "current_consumption": 570.0,
                "avg_consumption": 830.0,
                "power_factor": 0.80,
                "monthly_usage": [840, 820, 850, 810, 570],
                "theft_probability": 71.5,
                "risk_level": "Medium Risk",
                "deviation_percentage": -31.4,
                "is_suspicious": True,
                "status": "Active",
                "created_at": now - timedelta(hours=22)
            },
            {
                "consumer_id": "CN-88204",
                "consumer_name": "Consumer L",
                "sector": "Sector 4",
                "city": "Vadodara",
                "current_consumption": 620.0,
                "avg_consumption": 785.0,
                "power_factor": 0.84,
                "monthly_usage": [790, 770, 800, 780, 620],
                "theft_probability": 71.6,
                "risk_level": "Low Risk",
                "deviation_percentage": -21.0,
                "is_suspicious": True,
                "status": "Active",
                "created_at": now - timedelta(hours=23)
            }
        ]

        # 28 Resolved Cases
        resolved_cases = []
        for i in range(1, 29):
            resolved_cases.append({
                "consumer_id": f"CN-R{i:03d}",
                "consumer_name": f"Resolved Consumer {i}",
                "sector": f"Sector {i % 15 + 1}",
                "city": settings.DEFAULT_CITY if i % 2 == 0 else "Surat",
                "current_consumption": 850.0,
                "avg_consumption": 900.0,
                "power_factor": 0.92,
                "monthly_usage": [910, 890, 920, 880, 850],
                "theft_probability": 25.0 + (i % 20),
                "risk_level": "Normal",
                "deviation_percentage": -5.5,
                "is_suspicious": False,
                "status": "Resolved",
                "created_at": now - timedelta(days=2, hours=i)
            })

        for doc in active_suspicious + resolved_cases:
            doc["data_source"] = SOURCE_SEED_DATA
            await self.repository.save_alert(doc)
            
        logger.info("Successfully seeded 12 active and 28 resolved theft alerts.")
