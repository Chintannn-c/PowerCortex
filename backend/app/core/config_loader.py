import os
import yaml
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

class ConfigLoader:
    _instance = None
    _config_cache: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance._load_config()
            cls._instance._validate_config()
        return cls._instance

    def _load_config(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, 'config', 'production_config.yaml')
        
        try:
            with open(config_path, 'r') as f:
                self._config_cache = yaml.safe_load(f) or {}
                logger.info("Configuration successfully loaded and cached.")
        except FileNotFoundError:
            logger.error(f"Configuration file not found at {config_path}")
            raise RuntimeError(f"Startup Failed: Missing configuration file {config_path}")
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file: {e}")
            raise RuntimeError(f"Startup Failed: Malformed YAML in {config_path}")

    def _validate_config(self):
        # Fail-safe validation framework
        try:
            fault = self.get("fault_detection", {})
            if fault.get("frequency_high_threshold", 51.2) <= fault.get("frequency_low_threshold", 48.8):
                raise ValueError("frequency_high_threshold must be strictly greater than frequency_low_threshold")
            
            if fault.get("voltage_swell_threshold", 245.0) <= fault.get("voltage_sag_threshold", 195.0):
                raise ValueError("voltage_swell_threshold must be strictly greater than voltage_sag_threshold")
            
            renew = self.get("renewable", {})
            if renew.get("wind_cut_out_speed", 25.0) <= renew.get("wind_cut_in_speed", 3.5):
                raise ValueError("wind_cut_out_speed must be strictly greater than wind_cut_in_speed")
                
            trans = self.get("transformer", {})
            if trans.get("critical_temperature", 95) <= trans.get("warning_temperature", 85):
                raise ValueError("critical_temperature must be strictly greater than warning_temperature")
                
            logger.info("Configuration passed all fail-safe validations.")
        except Exception as e:
            logger.critical(f"Configuration Validation Failed: {e}")
            raise RuntimeError(f"Startup Blocked: Configuration is invalid -> {e}")

    def get(self, key_path: str, default: Any = None) -> Any:
        keys = key_path.split('.')
        val = self._config_cache
        for key in keys:
            if isinstance(val, dict):
                val = val.get(key)
                if val is None:
                    return default
            else:
                return default
        return val

    def reload(self):
        """Force a reload of the configuration from disk."""
        self._load_config()
        self._validate_config()

# Expose a global singleton instance
config = ConfigLoader()
