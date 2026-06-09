from datetime import datetime
import logging

logger = logging.getLogger("powercortex.ml.preprocess")

try:
    import pandas as pd
    import numpy as np
except ImportError:
    logger.warning("Pandas or NumPy not found. Feature engineering will fall back to native Python processing.")
    pd = None
    np = None

def extract_datetime_features(dt: datetime) -> dict:
    """Extract temporal features from a datetime object."""
    return {
        "hour": dt.hour,
        "day": dt.day,
        "weekday": dt.weekday(),
        "is_weekend": 1 if dt.weekday() >= 5 else 0,
        "month": dt.month,
        "day_of_week": dt.weekday(),
    }

def prepare_feature_vector(
    timestamp: datetime,
    historical_demand: list[float],
    temperature: float,
    humidity: int,
    wind_speed: float,
    cloud_cover: int,
    is_holiday: bool = False
) -> dict:
    """
    Constructs the feature vector required by the forecasting models.
    Supports native Python dict output and matches the model inputs.
    """
    dt_features = extract_datetime_features(timestamp)
    
    # Calculate rolling averages/lags from historical demand
    prev_hour_demand = historical_demand[-1] if historical_demand else 1350.0
    prev_day_demand = historical_demand[-24] if len(historical_demand) >= 24 else prev_hour_demand
    
    # Simple rolling moving averages
    moving_average_6h = sum(historical_demand[-6:]) / min(len(historical_demand), 6) if historical_demand else 1350.0
    moving_average_24h = sum(historical_demand[-24:]) / min(len(historical_demand), 24) if historical_demand else 1350.0
    
    features = {
        **dt_features,
        "temperature": temperature,
        "humidity": humidity,
        "wind_speed": wind_speed,
        "cloud_cover": cloud_cover,
        "holiday": 1 if is_holiday else 0,
        "prev_hour_demand": prev_hour_demand,
        "prev_day_demand": prev_day_demand,
        "moving_average_6h": moving_average_6h,
        "moving_average_24h": moving_average_24h,
    }
    
    return features

def convert_to_model_input(feature_dict: dict):
    """
    Converts features dictionary into a format ready for the ML model.
    Returns a pandas DataFrame or numpy array if pandas is available, otherwise returns the dictionary.
    """
    if pd is not None:
        try:
            return pd.DataFrame([feature_dict])
        except Exception as e:
            logger.error(f"Error converting to DataFrame: {e}")
    return feature_dict
