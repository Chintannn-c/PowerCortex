import logging
from ..utils.model_loader import ModelLoader
from ..core.config_loader import config

logger = logging.getLogger("powercortex.services.prediction")

class TransformerPredictionService:
    """Coordinates prediction execution, risk calculation, and status mapping."""

    @staticmethod
    def calculate_risk(health_score: float) -> float:
        """Calculates the risk score based on the health score."""
        return round(100.0 - health_score, 2)

    @staticmethod
    def get_status(health_score: float) -> str:
        """Determines asset status based on health score rules."""
        healthy_thresh = config.get("transformer.healthy_threshold", 80.0)
        warning_thresh = config.get("transformer.warning_threshold", 50.0)
        
        if health_score >= healthy_thresh:
            return "Healthy"
        elif health_score >= warning_thresh:
            return "Warning"
        else:
            return "Critical"
            
    @classmethod
    def run_inference(cls, temperature: float, voltage: float, current: float, oil_level: float, load_percentage: float) -> dict:
        """Runs the entire predictive pipeline for a given set of telemetry inputs."""
        health, failure_prob, prediction_source = ModelLoader.predict_transformer(
            temperature, voltage, current, oil_level, load_percentage
        )
        risk = cls.calculate_risk(health)
        status = cls.get_status(health)
        
        return {
            "health_score": health,
            "risk_score": risk,
            "failure_probability": failure_prob,
            "prediction_source": prediction_source,
            "status": status
        }
