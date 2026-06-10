"""
PowerCortex – Grid Constants & Thresholds

Centralized configuration for all magic numbers, thresholds, and
operational constants used across services. Reads from `production_config.yaml` 
if available in the environment to support dynamic configuration without code changes.
"""
import os
import yaml
import logging

logger = logging.getLogger("powercortex.core.grid_constants")

_config_cache = {}

def _load_yaml_config():
    global _config_cache
    if not _config_cache:
        config_path = os.path.join(os.path.dirname(__file__), 'production_config.yaml')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    _config_cache = yaml.safe_load(f) or {}
                logger.info(f"Loaded dynamic grid constants from {config_path}")
            except Exception as e:
                logger.error(f"Failed to load production_config.yaml: {e}")
                _config_cache = {}
        else:
            _config_cache = {}
    return _config_cache

def _get_val(key: str, default_val: float) -> float:
    """Helper to fetch from yaml or fallback to default."""
    config = _load_yaml_config()
    # Support both uppercase environment-style keys and lowercase yaml keys
    val = config.get(key.lower(), config.get(key.upper()))
    if val is not None:
        try:
            return float(val)
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to cast config value for {key} to float: {e}")
    return default_val


# ── Grid Demand Baselines ──────────────────────────────────────
GRID_BASELINE_DEMAND_MW: float = _get_val("GRID_BASELINE_DEMAND_MW", 41134.0)
GRID_PEAK_DEMAND_MW: float = _get_val("GRID_PEAK_DEMAND_MW", 42116.0)
GRID_MIN_DEMAND_MW: float = _get_val("GRID_MIN_DEMAND_MW", 28000.0)
GRID_MAX_DEMAND_MW: float = _get_val("GRID_MAX_DEMAND_MW", 48000.0)
HEURISTIC_FALLBACK_DEMAND_MW: float = _get_val("HEURISTIC_FALLBACK_DEMAND_MW", 30000.0)

# ── Forecast Metrics Baselines ──────────────────────────────────
FORECAST_DEFAULT_MAE: float = _get_val("FORECAST_DEFAULT_MAE", 481.72)
FORECAST_DEFAULT_RMSE: float = _get_val("FORECAST_DEFAULT_RMSE", 650.83)
FORECAST_DEFAULT_MAPE: float = _get_val("FORECAST_DEFAULT_MAPE", 1.54)
FORECAST_DEFAULT_CONFIDENCE_NEXT_HOUR: float = _get_val("FORECAST_DEFAULT_CONFIDENCE_NEXT_HOUR", 98.2)
FORECAST_DEFAULT_CONFIDENCE_NEXT_DAY: float = _get_val("FORECAST_DEFAULT_CONFIDENCE_NEXT_DAY", 95.4)
FORECAST_DEFAULT_CONFIDENCE_NEXT_WEEK: float = _get_val("FORECAST_DEFAULT_CONFIDENCE_NEXT_WEEK", 89.6)

# ── Renewable Capacity Limits ─────────────────────────────────
SOLAR_MAX_CAPACITY_MW: float = _get_val("SOLAR_MAX_CAPACITY_MW", 1200.0)
WIND_MAX_CAPACITY_MW: float = _get_val("WIND_MAX_CAPACITY_MW", 500.0)
RENEWABLE_DEFAULT_CONTRIB_PCT: float = _get_val("RENEWABLE_DEFAULT_CONTRIB_PCT", 38.0)
RENEWABLE_DEFAULT_SOLAR_MW: float = _get_val("RENEWABLE_DEFAULT_SOLAR_MW", 742.6)
RENEWABLE_DEFAULT_WIND_MW: float = _get_val("RENEWABLE_DEFAULT_WIND_MW", 312.4)
RENEWABLE_DEFAULT_TOTAL_MW: float = _get_val("RENEWABLE_DEFAULT_TOTAL_MW", 1055.0)

# Wind turbine physical limits
WIND_CUT_IN_SPEED_MS: float = _get_val("WIND_CUT_IN_SPEED_MS", 3.0)
WIND_CUT_OUT_SPEED_MS: float = _get_val("WIND_CUT_OUT_SPEED_MS", 25.0)

# ── Fault Detection Thresholds ────────────────────────────────
FREQUENCY_LOW_THRESHOLD: float = _get_val("FREQUENCY_LOW_THRESHOLD", 48.8)
FREQUENCY_HIGH_THRESHOLD: float = _get_val("FREQUENCY_HIGH_THRESHOLD", 51.2)
VOLTAGE_SAG_THRESHOLD: float = _get_val("VOLTAGE_SAG_THRESHOLD", 195.0)
VOLTAGE_SWELL_THRESHOLD: float = _get_val("VOLTAGE_SWELL_THRESHOLD", 245.0)
SHORT_CIRCUIT_VOLTAGE: float = _get_val("SHORT_CIRCUIT_VOLTAGE", 100.0)
SHORT_CIRCUIT_COMBO_VOLTAGE: float = _get_val("SHORT_CIRCUIT_COMBO_VOLTAGE", 160.0)
SHORT_CIRCUIT_COMBO_CURRENT: float = _get_val("SHORT_CIRCUIT_COMBO_CURRENT", 350.0)
EQUIPMENT_FAILURE_CURRENT: float = _get_val("EQUIPMENT_FAILURE_CURRENT", 500.0)
EQUIPMENT_FAILURE_VOLTAGE: float = _get_val("EQUIPMENT_FAILURE_VOLTAGE", 50.0)

# Fault severity probability thresholds
FAULT_CRITICAL_THRESHOLD: float = _get_val("FAULT_CRITICAL_THRESHOLD", 90.0)
FAULT_HIGH_THRESHOLD: float = _get_val("FAULT_HIGH_THRESHOLD", 75.0)
FAULT_MEDIUM_THRESHOLD: float = _get_val("FAULT_MEDIUM_THRESHOLD", 50.0)

# ── Theft Detection Thresholds ────────────────────────────────
THEFT_HIGH_RISK_PCT: float = _get_val("THEFT_HIGH_RISK_PCT", 90.0)
THEFT_MEDIUM_RISK_PCT: float = _get_val("THEFT_MEDIUM_RISK_PCT", 70.0)
THEFT_LOW_RISK_PCT: float = _get_val("THEFT_LOW_RISK_PCT", 50.0)
THEFT_NOTIFICATION_THRESHOLD: float = _get_val("THEFT_NOTIFICATION_THRESHOLD", 85.0)

# ── Transformer Health Thresholds ─────────────────────────────
TRANSFORMER_HEALTHY_THRESHOLD: float = _get_val("TRANSFORMER_HEALTHY_THRESHOLD", 80.0)
TRANSFORMER_WARNING_THRESHOLD: float = _get_val("TRANSFORMER_WARNING_THRESHOLD", 50.0)
TRANSFORMER_CRITICAL_TEMP: float = _get_val("TRANSFORMER_CRITICAL_TEMP", 95.0)
TRANSFORMER_WARNING_TEMP: float = _get_val("TRANSFORMER_WARNING_TEMP", 80.0)
TRANSFORMER_MIN_OIL_LEVEL: float = _get_val("TRANSFORMER_MIN_OIL_LEVEL", 80.0)
TRANSFORMER_OVERLOAD_PCT: float = _get_val("TRANSFORMER_OVERLOAD_PCT", 100.0)

# ── Caching ───────────────────────────────────────────────────
WEATHER_CACHE_DURATION_SECONDS: int = int(_get_val("WEATHER_CACHE_DURATION_SECONDS", 600))
FORECAST_CACHE_DURATION_MINUTES: int = int(_get_val("FORECAST_CACHE_DURATION_MINUTES", 10))

# ── Validation Consensus ─────────────────────────────────────
CONSENSUS_AGREEMENT_THRESHOLD: float = _get_val("CONSENSUS_AGREEMENT_THRESHOLD", 80.0)

# ── Prediction Source Labels (Static) ─────────────────────────
SOURCE_LSTM_MODEL = "lstm_model"
SOURCE_KERAS_DL_MODEL = "keras_dl_model"
SOURCE_KERAS_MLP_MODEL = "keras_mlp_model"
SOURCE_ISOLATION_FOREST = "isolation_forest_model"
SOURCE_HEURISTIC_FALLBACK = "heuristic_fallback"
SOURCE_RULE_BASED_FALLBACK = "rule_based_fallback"
SOURCE_HARDCODED_FALLBACK = "hardcoded_secondary"
SOURCE_SEED_DATA = "seed"
SOURCE_OPENWEATHERMAP = "openweathermap_api"
SOURCE_WEATHER_UNAVAILABLE = "unavailable"
SOURCE_MODEL_UNAVAILABLE = "model_unavailable"
SOURCE_DATA_UNAVAILABLE = "data_unavailable"
SOURCE_INCOMPLETE_DATA = "incomplete_data"
