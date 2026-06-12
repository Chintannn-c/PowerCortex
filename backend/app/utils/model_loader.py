import os
import json
import logging
import math
import time
from typing import Any
import pandas as pd
import numpy as np

from ..core.config import settings
from ..core.exceptions import ModelUnavailableError
from ..core.grid_constants import (
    GRID_BASELINE_DEMAND_MW,
    SOURCE_LSTM_MODEL, 
    SOURCE_KERAS_MLP_MODEL,
    SOURCE_ISOLATION_FOREST
)

logger = logging.getLogger("powercortex.ml.loader")

# Path to the LSTM trained model and dataset
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH = os.path.join(BASE_DIR, "data", "Electricity Demand Data", "lstm_demand_model.keras")
METADATA_PATH = os.path.join(BASE_DIR, "data", "Electricity Demand Data", "lstm_metadata.json")
HASHES_PATH = os.path.join(BASE_DIR, "models", "model_hashes.json")

from .model_security import verify_file_hash, load_model_hashes, SecurityError

class HeuristicDemandPredictor:
    """
    Deterministic demand estimator for explicitly enabled demo/development fallback mode.
    """
    def __init__(self, metadata_path: str = None) -> None:
        self.metadata = {}
        if metadata_path and os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    self.metadata = json.load(f)
                logger.info("Loaded LSTM metadata for heuristic simulation.")
            except Exception as e:
                logger.error(f"Failed to load metadata: {e}")

    def predict(self, features: dict) -> float:
        """
        Generates a highly realistic demand prediction in MW based on input features.
        Maps the baseline grid demand to the PJME state-wide grid range (20,000 to 45,000 MW).
        """
        hour = features.get("hour", 12)
        is_weekend = features.get("is_weekend", 0)
        temp = features.get("temperature", 25.0)
        prev_demand = features.get("prev_hour_demand", GRID_BASELINE_DEMAND_MW)
        
        # 1. Base demand level
        base_demand = GRID_BASELINE_DEMAND_MW
        
        # 2. Time-of-day pattern (Double peak: noon and evening)
        hour_factor = math.sin((hour - 4) * math.pi / 12) * 3500.0
        if 16 <= hour <= 21:
            hour_factor += 2000.0
        elif 2 <= hour <= 5:
            hour_factor -= 3000.0
            
        # 3. Weekend factor
        weekend_factor = -2500.0 if is_weekend == 1 else 0.0
        
        # 4. Temperature factor
        temp_factor = 0.0
        if temp > 22.0:
            temp_factor = (temp - 22.0) ** 1.3 * 400.0
        elif temp < 15.0:
            temp_factor = (15.0 - temp) * 250.0
            
        target_demand = base_demand + hour_factor + weekend_factor + temp_factor
        prediction = (prev_demand * 0.8) + (target_demand * 0.2)
        
        return round(max(15000.0, min(65000.0, prediction)), 2)


class ModelLoader:
    """Singleton class to load the dataset and manage the LSTM forecasting model."""
    _instance = None
    _model: Any = None
    _predictor: HeuristicDemandPredictor = None
    _forecast_recursive_tf: Any = None
    _predict_batch_tf: Any = None
    
    _transformer_model: Any = None
    _transformer_scaler: Any = None
    
    _fault_model: Any = None
    _fault_scaler: Any = None
    
    _theft_model: Any = None
    _theft_scaler: Any = None
    
    _system_health_model: Any = None
    _system_health_scaler: Any = None
    
    _model_hashes: dict = None
    
    # Evaluation metrics
    _mae: float = 481.72
    _rmse: float = 650.83
    _mape: float = 1.54

    # Dataset fields
    _df: pd.DataFrame = None
    _scaler_min: float = -0.30641525334456965
    _scaler_scale: float = 2.1068155482987463e-05

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ModelLoader, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    @classmethod
    def load_model(cls) -> None:
        """Loads the Keras model and initializes dataset at application startup."""
        if cls._df is None:
            cls.initialize_data()

        if cls._model is not None:
            return
            
        logger.info("Initializing demand forecasting model loader...")
        
        try:
            # Attempt to import TensorFlow and load the LSTM model
            import tensorflow as tf
            if os.path.exists(MODEL_PATH):
                if cls._model_hashes is None:
                    cls._model_hashes = load_model_hashes(HASHES_PATH)
                    
                logger.info(f"Loading Keras LSTM model from {MODEL_PATH}...")
                verify_file_hash(MODEL_PATH, cls._model_hashes)
                cls._model = tf.keras.models.load_model(MODEL_PATH)
                logger.info("LSTM model loaded successfully. Creating tf.functions...")
                
                # Define tf.functions to avoid python loop overhead in inference
                @tf.function(input_signature=[
                    tf.TensorSpec(shape=(1, 24, 1), dtype=tf.float32),
                    tf.TensorSpec(shape=(), dtype=tf.int32)
                ])
                def forecast_recursive(initial_sequence, steps):
                    current_seq = initial_sequence
                    predictions = tf.TensorArray(dtype=tf.float32, size=steps)
                    for i in tf.range(steps):
                        pred = cls._model(current_seq, training=False)
                        predictions = predictions.write(i, pred[0, 0])
                        next_step = tf.reshape(pred, (1, 1, 1))
                        current_seq = tf.concat([current_seq[:, 1:, :], next_step], axis=1)
                    return predictions.stack()

                @tf.function(input_signature=[
                    tf.TensorSpec(shape=(None, 24, 1), dtype=tf.float32)
                ])
                def predict_batch(input_batch):
                    return cls._model(input_batch, training=False)

                cls._forecast_recursive_tf = forecast_recursive
                cls._predict_batch_tf = predict_batch
                
                # Warm up functions
                logger.info("Warming up TensorFlow graph functions...")
                x_warmup = np.zeros((1, 24, 1), dtype=np.float32)
                _ = cls._forecast_recursive_tf(tf.convert_to_tensor(x_warmup), tf.constant(168))
                x_batch_warmup = np.zeros((24, 24, 1), dtype=np.float32)
                _ = cls._predict_batch_tf(tf.convert_to_tensor(x_batch_warmup))
                logger.info("TensorFlow graph functions warmed up.")
            else:
                logger.error("Demand LSTM model file not found at %s.", MODEL_PATH)
                if settings.ALLOW_MODEL_FALLBACKS:
                    logger.warning("ALLOW_MODEL_FALLBACKS is enabled. Using heuristic demand predictor.")
                    cls._predictor = HeuristicDemandPredictor(METADATA_PATH)
        except (ImportError, Exception) as e:
            logger.exception("TensorFlow could not initialize or demand model load failed.")
            cls._model = None
            cls._forecast_recursive_tf = None
            cls._predict_batch_tf = None
            if settings.ALLOW_MODEL_FALLBACKS:
                logger.warning("ALLOW_MODEL_FALLBACKS is enabled. Using heuristic demand predictor.")
                cls._predictor = HeuristicDemandPredictor(METADATA_PATH)

    @classmethod
    def initialize_data(cls) -> None:
        """Loads and prepares the PJME dataset in memory once at startup."""
        if cls._df is not None:
            return
            
        logger.info("Initializing PJME dataset loader...")
        try:
            csv_path = os.path.join(BASE_DIR, "data", "Electricity Demand Data", "data", "PJME_hourly.csv")
            if not os.path.exists(csv_path):
                logger.error(f"Dataset not found at {csv_path}!")
                return
                
            # Load and clean
            df = pd.read_csv(csv_path)
            df['Datetime'] = pd.to_datetime(df['Datetime'])
            df = df.sort_values('Datetime')
            df = df.groupby('Datetime').mean()
            
            full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq='h')
            df = df.reindex(full_range)
            df['PJME_MW'] = df['PJME_MW'].interpolate(method='linear')
            
            cls._df = df
            
            # Load scale metadata
            if os.path.exists(METADATA_PATH):
                with open(METADATA_PATH, 'r') as f:
                    meta = json.load(f)
                cls._scaler_min = meta["scaler"]["min"]
                cls._scaler_scale = meta["scaler"]["scale"]
                
                # Load evaluation metrics
                test_metrics = meta.get("metrics", {}).get("test", {})
                cls._mae = test_metrics.get("mae", 481.72)
                cls._rmse = test_metrics.get("rmse", 650.83)
                cls._mape = test_metrics.get("mape", 1.54)
                
                logger.info(f"Loaded scaler params: min={cls._scaler_min}, scale={cls._scaler_scale}")
                logger.info(f"Loaded model metrics: MAE={cls._mae}, RMSE={cls._rmse}, MAPE={cls._mape}")
            
            logger.info(f"Dataset loaded and preprocessed. Shape: {cls._df.shape}")
            
        except Exception as e:
            logger.error(f"Failed to load/preprocess dataset: {e}")

    @classmethod
    def get_model(cls) -> Any:
        """Returns the loaded Keras model if available, otherwise None."""
        return cls._model

    @classmethod
    def get_predictor(cls) -> HeuristicDemandPredictor:
        """Returns the fallback predictor."""
        if not settings.ALLOW_MODEL_FALLBACKS:
            raise ModelUnavailableError("Heuristic demand predictor is disabled. Configure the LSTM model or enable ALLOW_MODEL_FALLBACKS for demos.")
        if cls._predictor is None:
            cls._predictor = HeuristicDemandPredictor(METADATA_PATH)
        return cls._predictor

    @classmethod
    def get_target_idx(cls) -> int:
        """Returns the dynamic index in the test set representing 'now' (moving with time)."""
        if cls._df is None:
            cls.initialize_data()
        if cls._df is None:
            return 0
            
        # Split date threshold is 2016-01-01
        split_date = pd.to_datetime('2016-01-01')
        split_idx = cls._df.index.get_loc(split_date)
        test_size = len(cls._df) - split_idx
        
        current_seconds = int(time.time())
        # Use modulo to cycle through the test set (leave space for lookback and 168h future forecast)
        current_hour_idx = (current_seconds // 3600) % (test_size - 24 - 168)
        return split_idx + current_hour_idx

    @classmethod
    def predict_demand(cls, features: dict) -> tuple[float, str]:
        """
        Core interface to generate a prediction using either 
        the active deep learning model or the heuristic fallback.
        """
        if cls._model is None:
            cls.load_model()
            
        hist = features.get("historical_demand", [])
        if len(hist) < 24:
            if not settings.ALLOW_MODEL_FALLBACKS:
                raise ModelUnavailableError("Demand prediction requires at least 24 historical demand points.")
            hist = [GRID_BASELINE_DEMAND_MW] * 24
            
        hist = hist[-24:]
        scaled_seq = np.array(hist).reshape(-1, 1) * cls._scaler_scale + cls._scaler_min
        
        if cls._model is not None:
            try:
                # Shape for LSTM input: (1, 24, 1)
                input_seq = scaled_seq.reshape(1, 24, 1)
                import tensorflow as tf
                pred_scaled = cls._model(tf.convert_to_tensor(input_seq, dtype=tf.float32), training=False).numpy()[0][0]
                
                # Inverse scale
                pred_mw = (pred_scaled - cls._scaler_min) / cls._scaler_scale
                return float(round(pred_mw, 2)), SOURCE_LSTM_MODEL
            except Exception as e:
                logger.exception("Deep learning demand prediction failed.")
                if not settings.ALLOW_MODEL_FALLBACKS:
                    raise ModelUnavailableError("Demand LSTM inference failed and heuristic fallback is disabled.") from e
                
        if not settings.ALLOW_MODEL_FALLBACKS:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Demand LSTM model is not loaded. Ghost data disabled in production.")
        raise ModelUnavailableError("Ghost data disabled.")

    @classmethod
    def get_timeline_data(cls) -> list[dict]:
        """Returns actual vs predicted for the past 24 hours relative to target_idx."""
        if cls._df is None:
            cls.initialize_data()
        if cls._df is None:
            return []
            
        if cls._model is None:
            cls.load_model()
            
        if cls._model is None and not settings.ALLOW_MODEL_FALLBACKS:
            logger.error("Demand timeline prediction unavailable: LSTM model is not loaded.")
            return []
            
        target_idx = cls.get_target_idx()
        
        time_points = []
        actuals = []
        hist_sequences = []
        
        for i in range(target_idx - 23, target_idx + 1):
            time_points.append(cls._df.index[i])
            actuals.append(float(cls._df['PJME_MW'].iloc[i]))
            hist_sequences.append(cls._df['PJME_MW'].iloc[i-24:i].tolist())
            
        if cls._model is not None:
            try:
                import tensorflow as tf
                # Stack to (24, 24, 1) and scale
                hist_array = np.array(hist_sequences)
                scaled_batch = hist_array.reshape(24, 24, 1) * cls._scaler_scale + cls._scaler_min
                
                # Perform batch prediction in graph mode
                pred_tensors = cls._predict_batch_tf(tf.convert_to_tensor(scaled_batch, dtype=tf.float32))
                pred_scaled = pred_tensors.numpy()
                
                # Inverse scale
                pred_mws = (pred_scaled.flatten() - cls._scaler_min) / cls._scaler_scale
                predictions = [float(round(val, 2)) for val in pred_mws]
            except Exception as e:
                logger.exception("Batch prediction in timeline data failed.")
                from fastapi import HTTPException
                raise HTTPException(status_code=503, detail="Batch timeline prediction failed. Ghost data disabled in production.")
        else:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Demand LSTM model is not loaded. Ghost data disabled in production.")
                
        chart_points = []
        for idx in range(len(time_points)):
            chart_points.append({
                "timestamp": time_points[idx].isoformat(),
                "actual": actuals[idx],
                "predicted": predictions[idx]
            })
        return chart_points

    @classmethod
    def get_future_forecast(cls, hours: int = 168) -> list[dict]:
        """Runs recursive forecasting for the next `hours` hours starting from target_idx."""
        if cls._df is None:
            cls.initialize_data()
        if cls._df is None:
            return []
            
        if cls._model is None:
            cls.load_model()
            
        if cls._model is None and not settings.ALLOW_MODEL_FALLBACKS:
            logger.error("Future demand forecast unavailable: LSTM model is not loaded.")
            return []
            
        target_idx = cls.get_target_idx()
        hist = cls._df['PJME_MW'].iloc[target_idx-23:target_idx+1].tolist()
        
        scaled_seq = np.array(hist).reshape(-1, 1) * cls._scaler_scale + cls._scaler_min
        
        future_predictions = []
        
        if cls._model is not None:
            try:
                import tensorflow as tf
                # Perform recursive forecast in graph mode
                initial_seq = tf.convert_to_tensor(scaled_seq.reshape(1, 24, 1), dtype=tf.float32)
                pred_tensors = cls._forecast_recursive_tf(initial_seq, tf.constant(hours))
                pred_scaled = pred_tensors.numpy()
                
                # Inverse scale
                pred_mws = (pred_scaled - cls._scaler_min) / cls._scaler_scale
                future_predictions = [float(round(val, 2)) for val in pred_mws]
            except Exception as e:
                logger.exception("Recursive prediction in future forecast failed.")
                from fastapi import HTTPException
                raise HTTPException(status_code=503, detail="Recursive future forecast failed. Ghost data disabled in production.")
        else:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Demand LSTM model is not loaded. Ghost data disabled in production.")
            
        start_time = cls._df.index[target_idx] + pd.Timedelta(hours=1)
        forecast_points = []
        for h, val in enumerate(future_predictions):
            time_point = start_time + pd.Timedelta(hours=h)
            forecast_points.append({
                "timestamp": time_point,
                "predicted": float(round(val, 2))
            })
            
        return forecast_points

    @classmethod
    def load_transformer_model(cls) -> None:
        """Loads the Keras MLP transformer health model once at startup."""
        if cls._transformer_model is not None:
            return
            
        import pickle
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(base_dir, "models", "transformer_health_model.keras")
        scaler_path = os.path.join(base_dir, "models", "transformer_scaler.pkl")
        
        logger.info(f"Checking for transformer Keras model at {model_path}...")
        if os.path.exists(model_path) and os.path.exists(scaler_path):
            try:
                if cls._model_hashes is None:
                    cls._model_hashes = load_model_hashes(HASHES_PATH)
                    
                verify_file_hash(model_path, cls._model_hashes)
                verify_file_hash(scaler_path, cls._model_hashes)
                
                import tensorflow as tf
                cls._transformer_model = tf.keras.models.load_model(model_path)
                with open(scaler_path, 'rb') as f:
                    cls._transformer_scaler = pickle.load(f)  # nosec B301
                logger.info("Transformer health Keras model and scaler loaded successfully.")
            except Exception as e:
                logger.exception("Failed to load transformer Keras model.")
                cls._transformer_model = None
                cls._transformer_scaler = None
        else:
            logger.warning("Transformer health Keras model or scaler files not found.")

    @classmethod
    def predict_transformer(cls, temperature: float, voltage: float, current: float, oil_level: float, load_percentage: float) -> tuple[float, float, str]:
        """Runs inference using Keras MLP model or fallback heuristics."""
        if cls._transformer_model is None:
            cls.load_transformer_model()
            
        if cls._transformer_model is not None and cls._transformer_scaler is not None:
            try:
                import tensorflow as tf
                features = np.array([[temperature, voltage, current, oil_level, load_percentage]])
                scaled_features = cls._transformer_scaler.transform(features)
                preds = cls._transformer_model(tf.convert_to_tensor(scaled_features, dtype=tf.float32), training=False).numpy()
                health_score = float(preds[0][0])
                failure_prob = float(preds[0][1])
                return round(health_score, 2), round(failure_prob, 2), SOURCE_KERAS_MLP_MODEL
            except Exception as e:
                logger.exception("Keras MLP transformer prediction failed.")
                if not settings.ALLOW_MODEL_FALLBACKS:
                    raise ModelUnavailableError("Transformer health model inference failed and fallback is disabled.") from e
                
        # High-fidelity fallback heuristics if model loading fails
        if not settings.ALLOW_MODEL_FALLBACKS:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Transformer health model is not loaded. Ghost data disabled in production.")
        raise ModelUnavailableError("Ghost data disabled.")

    @classmethod
    def load_fault_model(cls) -> None:
        """Loads the Keras fault detection model once at startup."""
        if cls._fault_model is not None:
            return
            
        import pickle
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(base_dir, "models", "fault_detection_model.keras")
        scaler_path = os.path.join(base_dir, "models", "fault_scaler.pkl")
        
        logger.info(f"Checking for fault detection Keras model at {model_path}...")
        if os.path.exists(model_path) and os.path.exists(scaler_path):
            try:
                if cls._model_hashes is None:
                    cls._model_hashes = load_model_hashes(HASHES_PATH)
                    
                verify_file_hash(model_path, cls._model_hashes)
                verify_file_hash(scaler_path, cls._model_hashes)
                
                import tensorflow as tf
                cls._fault_model = tf.keras.models.load_model(model_path)
                with open(scaler_path, 'rb') as f:
                    cls._fault_scaler = pickle.load(f)  # nosec B301
                logger.info("Fault detection Keras model and scaler loaded successfully.")
            except Exception as e:
                logger.exception("Failed to load fault detection Keras model.")
                cls._fault_model = None
                cls._fault_scaler = None
        else:
            logger.warning("Fault detection Keras model or scaler files not found.")

    @classmethod
    def predict_fault(cls, voltage: float, current: float, frequency: float) -> tuple[int, float, str]:
        """Runs inference using Keras MLP model to predict fault type label and confidence probability."""
        if cls._fault_model is None:
            cls.load_fault_model()
            
        if cls._fault_model is not None and cls._fault_scaler is not None:
            try:
                import tensorflow as tf
                # Handle current scaling mismatch (if in Amperes instead of scaled/kA unit)
                if current > 60.0:
                    current = current / 10.0
                    
                features = np.array([[voltage, current, frequency]])
                scaled_features = cls._fault_scaler.transform(features)
                
                # Inference using Keras model
                tensor_input = tf.convert_to_tensor(scaled_features, dtype=tf.float32)
                probs_tensor = cls._fault_model(tensor_input, training=False)
                probs = probs_tensor.numpy()[0]
                
                pred_label = int(np.argmax(probs))
                probability = float(probs[pred_label]) * 100.0
                
                return pred_label, round(probability, 2), SOURCE_KERAS_MLP_MODEL
            except Exception as e:
                logger.exception("Keras fault prediction failed.")
                if not settings.ALLOW_MODEL_FALLBACKS:
                    raise ModelUnavailableError("Fault detection model inference failed and rule-based fallback is disabled.") from e
                
        # High-fidelity rule-based fallback if model is not loaded
        if not settings.ALLOW_MODEL_FALLBACKS:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Fault detection model is not loaded. Ghost data disabled in production.")
        raise ModelUnavailableError("Ghost data disabled.")

    @classmethod
    def load_theft_model(cls) -> None:
        """Loads the Keras Autoencoder theft detection model once at startup."""
        if cls._theft_model is not None:
            return
            
        import pickle
        import json
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(base_dir, "models", "theft_detection_model.keras")
        scaler_path = os.path.join(base_dir, "models", "theft_scaler.pkl")
        threshold_path = os.path.join(base_dir, "models", "theft_threshold.json")
        
        logger.info(f"Checking for theft detection Keras model at {model_path}...")
        if os.path.exists(model_path) and os.path.exists(scaler_path):
            try:
                if cls._model_hashes is None:
                    cls._model_hashes = load_model_hashes(HASHES_PATH)
                    
                verify_file_hash(model_path, cls._model_hashes)
                verify_file_hash(scaler_path, cls._model_hashes)
                
                import tensorflow as tf
                cls._theft_model = tf.keras.models.load_model(model_path)
                with open(scaler_path, 'rb') as f:
                    cls._theft_scaler = pickle.load(f)  # nosec B301
                
                cls._theft_threshold = 0.5  # fallback
                if os.path.exists(threshold_path):
                    with open(threshold_path, 'r') as f:
                        meta = json.load(f)
                        cls._theft_threshold = meta.get("mse_threshold", 0.5)
                        
                logger.info("Theft detection Keras Autoencoder and scaler loaded successfully.")
            except Exception as e:
                logger.exception("Failed to load theft detection Keras model.")
                cls._theft_model = None
                cls._theft_scaler = None
                cls._theft_threshold = None
        else:
            logger.warning("Theft detection model or scaler files not found.")

    @classmethod
    def predict_theft(cls, current_consumption: float, avg_consumption: float, power_factor: float) -> tuple[float, bool, float, str]:
        """
        Runs inference using Keras Autoencoder to predict theft probability, suspicion state, and deviation percentage.
        Returns: tuple[theft_probability: float, is_suspicious: bool, deviation_percentage: float]
        """
        # Calculate deviation percentage: ((current_consumption - avg_consumption) / avg_consumption) * 100
        deviation = 0.0
        if avg_consumption > 0:
            deviation = ((current_consumption - avg_consumption) / avg_consumption) * 100.0
            
        # Ensure deviation is rounded to 1 decimal place
        deviation = round(deviation, 1)
        
        # Default fallback values
        is_suspicious = False
        probability = 15.0  # Normal base probability
        
        if cls._theft_model is None:
            cls.load_theft_model()
            
        if cls._theft_model is not None and cls._theft_scaler is not None:
            try:
                import tensorflow as tf
                features = np.array([[current_consumption, avg_consumption, power_factor, deviation]])
                scaled_features = cls._theft_scaler.transform(features)
                
                # Autoencoder reconstructs the input
                pred_features = cls._theft_model(tf.convert_to_tensor(scaled_features, dtype=tf.float32), training=False).numpy()
                
                # Calculate Mean Squared Error (MSE) reconstruction loss
                mse_loss = float(np.mean(np.power(scaled_features - pred_features, 2), axis=1)[0])
                threshold = getattr(cls, '_theft_threshold', 0.5)
                
                if mse_loss > threshold:
                    is_suspicious = True
                    # Scale loss to probability between 60% and 99%
                    ratio = min(mse_loss / threshold, 3.0)  # cap at 3x threshold
                    prob_val = 60.0 + ((ratio - 1.0) / 2.0) * 39.0
                    probability = min(99.0, max(60.0, prob_val))
                else:
                    is_suspicious = False
                    # Scale loss to probability between 5% and 49%
                    ratio = mse_loss / threshold
                    prob_val = 5.0 + (ratio * 44.0)
                    probability = min(49.0, max(5.0, prob_val))
                    
                return round(probability, 1), is_suspicious, deviation, SOURCE_KERAS_MLP_MODEL
            except Exception as e:
                logger.exception("Keras Autoencoder theft prediction failed.")
                if not settings.ALLOW_MODEL_FALLBACKS:
                    raise ModelUnavailableError("Theft detection model inference failed and heuristic fallback is disabled.") from e
                
        # High-fidelity fallback heuristic if model is not loaded
        if not settings.ALLOW_MODEL_FALLBACKS:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Theft detection model is not loaded. Ghost data disabled in production.")
        raise ModelUnavailableError("Ghost data disabled.")

    @classmethod
    def load_system_health_model(cls) -> None:
        """Loads the Keras MLP system health model once at startup."""
        if cls._system_health_model is not None:
            return
            
        import pickle
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(base_dir, "models", "system_health_model.keras")
        scaler_path = os.path.join(base_dir, "models", "system_health_scaler.pkl")
        
        logger.info(f"Checking for system health Keras model at {model_path}...")
        if os.path.exists(model_path) and os.path.exists(scaler_path):
            try:
                if cls._model_hashes is None:
                    cls._model_hashes = load_model_hashes(HASHES_PATH)
                    
                verify_file_hash(model_path, cls._model_hashes)
                verify_file_hash(scaler_path, cls._model_hashes)
                
                import tensorflow as tf
                cls._system_health_model = tf.keras.models.load_model(model_path)
                with open(scaler_path, 'rb') as f:
                    cls._system_health_scaler = pickle.load(f)  # nosec B301
                logger.info("System health Keras model and scaler loaded successfully.")
            except Exception as e:
                logger.exception("Failed to load system health Keras model.")
                cls._system_health_model = None
                cls._system_health_scaler = None
        else:
            logger.warning("System health Keras model or scaler files not found.")

    @classmethod
    def predict_system_health(cls, cpu_usage: float, memory_usage: float, network_latency: float, db_connected: float, api_latency: float) -> tuple[float, float]:
        """Runs inference using Keras MLP model to predict system health score and failure probability."""
        if cls._system_health_model is None:
            cls.load_system_health_model()
            
        if cls._system_health_model is not None and cls._system_health_scaler is not None:
            try:
                import tensorflow as tf
                features = np.array([[cpu_usage, memory_usage, network_latency, db_connected, api_latency]])
                scaled_features = cls._system_health_scaler.transform(features)
                preds = cls._system_health_model(tf.convert_to_tensor(scaled_features, dtype=tf.float32), training=False).numpy()
                health_score = float(preds[0][0])
                failure_prob = float(preds[0][1])
                return round(max(0.0, min(100.0, health_score)), 2), round(max(0.0, min(99.0, failure_prob)), 2)
            except Exception as e:
                logger.exception("Keras system health prediction failed.")
                if not settings.ALLOW_MODEL_FALLBACKS:
                    raise ModelUnavailableError("System health model inference failed and fallback is disabled.") from e
                
        # High-fidelity fallback heuristics if model is not loaded
        if not settings.ALLOW_MODEL_FALLBACKS:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="System health model is not loaded. Ghost data disabled in production.")
        raise ModelUnavailableError("Ghost data disabled.")
