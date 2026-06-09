import os
import logging
import joblib
import numpy as np
from ..core.config import settings
from ..core.exceptions import ModelUnavailableError
from ..core.config_loader import config
from ..core.grid_constants import (
    SOURCE_KERAS_DL_MODEL,
    SOURCE_HEURISTIC_FALLBACK,
)

logger = logging.getLogger("powercortex.ml.renewable_predictor")

class RenewablePredictor:
    _solar_model = None
    _wind_model = None
    _scaler = None
    _models_loaded = False

    @classmethod
    def load_models(cls):
        if cls._models_loaded:
            return True
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            solar_path = os.path.join(base_dir, "models", "solar_forecast_model.keras")
            wind_path = os.path.join(base_dir, "models", "wind_forecast_model.keras")
            scaler_path = os.path.join(base_dir, "models", "renewable_scaler.pkl")

            if os.path.exists(solar_path) and os.path.exists(wind_path) and os.path.exists(scaler_path):
                import tensorflow as tf
                # Disable TF warnings
                os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
                
                cls._solar_model = tf.keras.models.load_model(solar_path)
                cls._wind_model = tf.keras.models.load_model(wind_path)
                cls._scaler = joblib.load(scaler_path)
                cls._models_loaded = True
                logger.info("Renewable forecasting Keras DL models loaded successfully.")
                return True
            else:
                logger.warning("Renewable DL models or scaler not found in %s/models/", base_dir)
                return False
        except Exception:
            logger.exception("Error loading renewable forecasting DL models.")
            return False

    @classmethod
    def _heuristic_predict(cls, temp: float, humidity: float, wind_speed: float, cloud_cover: float, city: str = "ahmedabad"):
        """Physics-based heuristic fallback. Returns (solar, wind)."""
        solar_gen = 1787.57 * (1.0 - cloud_cover / 100.0) * (1.0 - 0.005 * abs(temp - 25.0)) * (1.0 - 0.002 * humidity)
        wind_gen = 321.4 * (wind_speed / 13.0) ** 2 * (1.0 - 0.002 * abs(temp - 20.0))
        
        wind_cut_in = config.get("renewable.wind_cut_in_speed", 3.5)
        wind_cut_out = config.get("renewable.wind_cut_out_speed", 25.0)
        
        if wind_speed < wind_cut_in or wind_speed > wind_cut_out:
            wind_gen = 0.0

        solar_cap = config.get(f"renewable.regions.gujarat.{city}.solar_capacity_mw", 5000.0)
        wind_cap = config.get(f"renewable.regions.gujarat.{city}.wind_capacity_mw", 2000.0)

        solar_gen = max(0.0, min(solar_cap, solar_gen))
        wind_gen = max(0.0, min(wind_cap, wind_gen))
        return round(solar_gen, 1), round(wind_gen, 1)

    @classmethod
    def predict_renewables(cls, temp: float, humidity: float, wind_speed: float, cloud_cover: float, city: str = "ahmedabad"):
        """
        Predict solar and wind generation.
        Returns: (solar_mw, wind_mw, prediction_source)
        """
        cls.load_models()
        
        if not cls._models_loaded:
            if not settings.ALLOW_MODEL_FALLBACKS:
                raise ModelUnavailableError("Renewable DL models are not loaded and heuristic fallback is disabled.")
            solar_gen, wind_gen = cls._heuristic_predict(temp, humidity, wind_speed, cloud_cover, city)
            return solar_gen, wind_gen, SOURCE_HEURISTIC_FALLBACK

        try:
            # Scale features
            features = np.array([[temp, humidity, wind_speed, cloud_cover]], dtype=np.float32)
            scaled_features = cls._scaler.transform(features)
            
            # Keras inference
            solar_pred = cls._solar_model(scaled_features, training=False).numpy()[0][0]
            wind_pred = cls._wind_model(scaled_features, training=False).numpy()[0][0]
            
            # Post-processing physics checks
            wind_cut_in = config.get("renewable.wind_cut_in_speed", 3.5)
            wind_cut_out = config.get("renewable.wind_cut_out_speed", 25.0)
            
            if wind_speed < wind_cut_in or wind_speed > wind_cut_out:
                wind_pred = 0.0
            if cloud_cover > 98.0:
                solar_pred = min(solar_pred, 5.0)  # very low solar output under dense cloud cover
                
            solar_cap = config.get(f"renewable.regions.gujarat.{city}.solar_capacity_mw", 5000.0)
            wind_cap = config.get(f"renewable.regions.gujarat.{city}.wind_capacity_mw", 2000.0)
                
            solar_pred = max(0.0, min(solar_cap, float(solar_pred)))
            wind_pred = max(0.0, min(wind_cap, float(wind_pred)))
            
            return round(solar_pred, 1), round(wind_pred, 1), SOURCE_KERAS_DL_MODEL
        except Exception as exc:
            logger.exception("Error during renewable DL model inference.")
            if not settings.ALLOW_MODEL_FALLBACKS:
                raise ModelUnavailableError("Renewable DL inference failed and heuristic fallback is disabled.") from exc
            solar_gen, wind_gen = cls._heuristic_predict(temp, humidity, wind_speed, cloud_cover, city)
            return solar_gen, wind_gen, SOURCE_HEURISTIC_FALLBACK
