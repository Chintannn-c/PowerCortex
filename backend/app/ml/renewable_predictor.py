import os
import logging
import joblib
import numpy as np
from ..core.config import settings
from ..core.exceptions import ModelUnavailableError
from ..core.config_loader import config
from ..core.grid_constants import (
    SOURCE_KERAS_DL_MODEL,
)

from ..utils.model_security import verify_file_hash, load_model_hashes, SecurityError

logger = logging.getLogger("powercortex.ml.renewable_predictor")

class RenewablePredictor:
    _solar_model = None
    _wind_model = None
    _scaler = None
    _models_loaded = False
    _model_hashes = None

    @classmethod
    def load_models(cls):
        if cls._models_loaded:
            return True
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            solar_path = os.path.join(base_dir, "models", "solar_forecast_model.keras")
            wind_path = os.path.join(base_dir, "models", "wind_forecast_model.keras")
            scaler_path = os.path.join(base_dir, "models", "renewable_scaler.pkl")
            hashes_path = os.path.join(os.path.dirname(base_dir), "models", "model_hashes.json")

            if os.path.exists(solar_path) and os.path.exists(wind_path) and os.path.exists(scaler_path):
                if cls._model_hashes is None:
                    cls._model_hashes = load_model_hashes(hashes_path)
                
                verify_file_hash(solar_path, cls._model_hashes)
                verify_file_hash(wind_path, cls._model_hashes)
                verify_file_hash(scaler_path, cls._model_hashes)

                import tensorflow as tf
                # Disable TF warnings
                os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
                
                cls._solar_model = tf.keras.models.load_model(solar_path)
                cls._wind_model = tf.keras.models.load_model(wind_path)
                cls._scaler = joblib.load(scaler_path)
                cls._models_loaded = True
                logger.info("Renewable forecasting Keras DL models verified and loaded successfully.")
                return True
            else:
                logger.warning("Renewable DL models or scaler not found in %s/models/", base_dir)
                return False
        except SecurityError as se:
            logger.error(f"Security violation during renewable model verification: {se}")
            raise
        except Exception:
            logger.exception("Error loading renewable forecasting DL models.")
            return False

    @classmethod
    def predict_renewables(cls, temp: float, humidity: float, wind_speed: float, cloud_cover: float, city: str = "ahmedabad"):
        """
        Predict solar and wind generation.
        Returns: (solar_mw, wind_mw, prediction_source)
        """
        cls.load_models()
        
        if not cls._models_loaded:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Renewable DL models are not loaded and ghost data fallbacks are disabled in production.")

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
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Renewable DL inference failed. Ghost data fallbacks disabled.") from exc
