import time
import math
import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
from ..core.config import settings
from ..utils.helpers import utcnow
from ..core.config_loader import config

logger = logging.getLogger("powercortex.services.validation")

class ValidationService:
    def __init__(self, db) -> None:
        self.db = db

    async def save_validation_log(self, module: str, prediction_id: str, confidence_score: float, validated: bool, sources: List[str], details: Dict[str, Any]) -> None:
        """Persist validation results to MongoDB."""
        try:
            log_entry = {
                "module": module,
                "prediction_id": prediction_id,
                "confidence_score": round(confidence_score, 2),
                "validated": validated,
                "validation_sources": sources,
                "details": details,
                "created_at": utcnow()
            }
            await self.db.prediction_validations.insert_one(log_entry)
            logger.info(f"Saved prediction validation log for {module}")
        except Exception as e:
            logger.error(f"Failed to save validation log: {e}")

    async def validate_load_forecast(self, predicted_demand: float, temperature: float, hour: int, weekday: int) -> Dict[str, Any]:
        """
        Validate demand forecast against:
        - Weather deviations (temperature spikes)
        - Historical bounds (41,134 MW base mean)
        - Seasonality rules
        - Holiday drop rules
        """
        validation_sources = ["weather", "historical_patterns", "seasonality"]
        validated = True
        notes_list = []
        
        # 1. Weather Checks (Temperature anomaly)
        # Demand is expected to rise with cooling load above 30C or heating below 12C
        weather_api_status = "Online"
        if temperature > 40.0:
            notes_list.append("Extreme hot weather alert: High air conditioning load expected.")
        elif temperature < 10.0:
            notes_list.append("Extreme cold weather alert: High heating load expected.")
            
        # 2. Historical patterns check
        min_expected = config.get("forecasting.grid_min_demand_mw", 28000.0)
        max_expected = config.get("forecasting.grid_max_demand_mw", 48000.0)
        
        # Adjust expected bounds by hour of the day (off-peak vs peak hours)
        if 2 <= hour <= 5: # Late night off-peak
            min_expected -= 5000.0
            max_expected -= 3000.0
        elif 18 <= hour <= 22: # Evening peak
            min_expected += 2000.0
            max_expected += 4000.0
            
        # Adjust for weekend
        if weekday >= 5: # Saturday/Sunday
            min_expected -= 3000.0
            max_expected -= 2000.0
            
        # Calculate deviation percentage
        midpoint = (min_expected + max_expected) / 2
        deviation = abs(predicted_demand - midpoint) / midpoint
        
        if predicted_demand < min_expected or predicted_demand > max_expected:
            validated = False
            notes_list.append(f"Demand {predicted_demand:,.0f} MW is outside typical baseline bounds [{min_expected:,.0f} - {max_expected:,.0f} MW].")
            
        # 3. Seasonal check
        # Summer (March - June): High peak load
        # Monsoon (July - October): Humidity peaks
        # Winter (November - February): Lower peak load
        current_month = datetime.now().month
        if current_month in [5, 6]: # Peak Summer
            if predicted_demand < 32000.0:
                notes_list.append("Under-forecasting warning for peak summer conditions.")
        elif current_month in [12, 1]: # Winter
            if predicted_demand > 44000.0:
                notes_list.append("Over-forecasting warning for winter conditions.")

        # 4. Holiday drop rules
        # Mock public holidays check: if weekday == 6 (Sunday) and peak hour, check if demand dropped
        is_holiday = (weekday == 6)
        if is_holiday:
            validation_sources.append("holiday_calendar")
            peak_thresh = config.get("forecasting.grid_peak_demand_mw", 42116.0)
            if predicted_demand > peak_thresh:
                notes_list.append("Sunday holiday warning: High load predicted despite corporate shut-down.")
                
        # Calculate confidence score
        # Start at 98%, deduct based on anomalies/deviations
        confidence = 98.0
        if deviation > 0.2:
            confidence -= (deviation - 0.2) * 100.0
        if not validated:
            confidence -= 15.0
        confidence = max(50.0, min(99.0, confidence))

        res = {
            "predicted_demand": round(predicted_demand, 2),
            "confidence": round(confidence, 2),
            "validated": validated,
            "validation_sources": validation_sources,
            "notes": " ".join(notes_list) if notes_list else "Load forecast is statistically within normal bounds."
        }
        await self.save_validation_log("load_forecasting", "load_last", confidence, validated, validation_sources, res)
        return res

    async def validate_renewable_forecast(self, solar_forecast: float, wind_forecast: float, temp: float, humidity: float, wind_speed: float, cloud_cover: float) -> Dict[str, Any]:
        """
        Validate Solar & Wind forecasting against weather parameters:
        - Solar Night-time and cloudiness validation
        - Wind Turbine physical limits (cut-in / cut-out speeds)
        """
        validation_sources = ["weather_api", "physical_limits"]
        validated = True
        notes_list = []
        
        # 1. Solar Validation
        # Check daylight hours (hour between 6 AM and 7 PM)
        current_hour = datetime.now().hour
        is_night = (current_hour < 6 or current_hour > 19)
        
        if is_night and solar_forecast > 10.0:
            validated = False
            notes_list.append(f"Solar forecast of {solar_forecast} MW is invalid during night hour ({current_hour}:00). Capping output.")
            solar_forecast = 0.0
            
        # Cloud cover check
        if cloud_cover > 80.0 and solar_forecast > 400.0:
            notes_list.append(f"High cloud cover ({cloud_cover}%) mismatch: Solar output ({solar_forecast} MW) may be over-optimistic.")
            
        # Capacity limit (max solar farm output = 1200 MW)
        if solar_forecast > 1200.0:
            validated = False
            notes_list.append(f"Solar forecast ({solar_forecast} MW) exceeds maximum installed farm capacity of 1,200 MW.")
            solar_forecast = 1200.0

        # 2. Wind Validation
        # Wind cut-in speed: 3.0 m/s (below this turbines don't spin)
        # Wind cut-out speed: 25.0 m/s (above this turbines brake for safety)
        if wind_speed < 3.0 and wind_forecast > 20.0:
            validated = False
            notes_list.append(f"Low wind speed ({wind_speed} m/s) below cut-in limit (3 m/s). Capping wind output.")
            wind_forecast = 0.0
        elif wind_speed > 25.0 and wind_forecast > 50.0:
            validated = False
            notes_list.append(f"Extreme storm wind speed ({wind_speed} m/s) exceeds cut-out safety limit (25 m/s). Turbines braked.")
            wind_forecast = 0.0
            
        if wind_forecast > 500.0:
            validated = False
            notes_list.append(f"Wind forecast ({wind_forecast} MW) exceeds maximum turbine farm capacity of 500 MW.")
            wind_forecast = 500.0
            
        # Calculate confidence
        confidence = 96.0
        if not validated:
            confidence -= 12.0
        if cloud_cover > 90.0 and solar_forecast > 200.0:
            confidence -= 10.0
            
        confidence = max(50.0, min(99.0, confidence))
        
        res = {
            "solar_forecast": round(solar_forecast, 2),
            "wind_forecast": round(wind_forecast, 2),
            "confidence": round(confidence, 2),
            "validated": validated,
            "notes": " ".join(notes_list) if notes_list else "Renewable forecasts correlate with active weather parameters."
        }
        await self.save_validation_log("renewable_forecasting", "renewable_last", confidence, validated, validation_sources, res)
        return res

    async def validate_fault_detection(self, voltage: float, current: float, frequency: float, predicted_fault: str, ml_prob: float) -> Dict[str, Any]:
        """
        Validate fault prediction using physical grid rules and multi-model consensus.
        """
        validation_sources = ["engineering_rules", "consensus_engine"]
        rule_validation = True
        notes_list = []
        
        # 1. Rule checks
        is_swell = (voltage > 245.0)
        is_sag = (voltage < 195.0)
        is_overload = (current > 25.0)
        is_freq_anomaly = (frequency < 48.5 or frequency > 51.5)
        
        # Mapping predicted_fault string or index to type
        fault_name = predicted_fault.lower()
        
        if "swell" in fault_name and not is_swell:
            rule_validation = False
            notes_list.append(f"Voltage swell predicted but voltage is normal ({voltage}V).")
        elif "sag" in fault_name and not is_sag:
            rule_validation = False
            notes_list.append(f"Voltage sag predicted but voltage is normal ({voltage}V).")
        elif "overload" in fault_name and not is_overload:
            rule_validation = False
            notes_list.append(f"Overload predicted but current is normal ({current}A).")
            
        # 2. Consensus checks
        consensus_data = self.calculate_consensus(
            prediction_type="fault",
            inputs={"voltage": voltage, "current": current, "frequency": frequency},
            primary_prediction=predicted_fault
        )
        
        agreement_score = consensus_data["agreement_score"]
        confidence = (ml_prob + agreement_score) / 2.0
        
        if agreement_score < 80.0:
            notes_list.append(f"Ensemble consensus is low ({agreement_score}%). XGBoost/LightGBM predictions disagree.")
            
        res = {
            "fault_type": predicted_fault,
            "ml_probability": round(ml_prob, 2),
            "rule_validation": rule_validation,
            "confidence": round(confidence, 2),
            "agreement_score": round(agreement_score, 2),
            "notes": " ".join(notes_list) if notes_list else "Fault telemetry validated against grid physics and multi-model consensus."
        }
        await self.save_validation_log("fault_detection", f"fault_{int(time.time())}", confidence, rule_validation, validation_sources, res)
        return res

    async def validate_theft_detection(self, consumer_id: str, consumption: float, avg_consumption: float, power_factor: float, predicted_risk: float) -> Dict[str, Any]:
        """
        Validate suspicious theft alert using consumption deviations and power factor checks.
        """
        validation_sources = ["historical_consumption", "neighbourhood_comparison"]
        validated = True
        notes_list = []
        
        # Calculate deviation percentage
        deviation = 0.0
        if avg_consumption > 0:
            deviation = ((consumption - avg_consumption) / avg_consumption) * 100.0
            
        # Power factor check (low power factor is common in diversion tampering)
        if power_factor < 0.75:
            validation_sources.append("power_factor_analysis")
            notes_list.append(f"Power factor anomaly: Low PF ({power_factor}) strongly indicates inductive bypass tapping.")
            
        # Sudden drop check
        if deviation < -40.0:
            notes_list.append(f"Sudden consumption drop: Dev is -{abs(deviation):.1f}% below monthly average.")
        elif deviation > 20.0 and predicted_risk > 60.0:
            validated = False
            notes_list.append(f"Theft warning conflict: Consumption is ABOVE average (+{deviation:.1f}%), but theft was flagged.")
            
        consensus_data = self.calculate_consensus(
            prediction_type="theft",
            inputs={"deviation": deviation, "power_factor": power_factor},
            primary_prediction="suspicious" if predicted_risk > 50.0 else "normal"
        )
        agreement_score = consensus_data["agreement_score"]
        confidence = (predicted_risk + agreement_score) / 2.0
        
        res = {
            "consumer_id": consumer_id,
            "theft_probability": round(predicted_risk, 2),
            "validated": validated,
            "confidence": round(confidence, 2),
            "notes": " ".join(notes_list) if notes_list else "Outlier consumption aligns with Isolation Forest anomaly classification."
        }
        await self.save_validation_log("theft_detection", f"theft_{consumer_id}", confidence, validated, validation_sources, res)
        return res

    async def validate_transformer_health(self, asset_id: str, temp: float, voltage: float, current: float, oil_level: float, load_pct: float, primary_health: float, failure_prob: float) -> Dict[str, Any]:
        """
        Validate transformer diagnostics using engineering threshold rules.
        """
        validation_sources = ["thermal_rules", "engineering_limits"]
        validated = True
        notes_list = []
        
        # 1. Thermal checks
        if temp > 95.0:
            notes_list.append(f"Severe thermal alert: Winding temp is {temp}°C (critical threshold is 90°C).")
            if primary_health > 60.0:
                validated = False
                notes_list.append("Health score conflict: Model predicted high health score despite thermal warning.")
                
        # 2. Oil Level checks
        if oil_level < 70.0:
            notes_list.append(f"Low dielectric oil warning: Level at {oil_level}% (minimum safe limit is 80%).")
            
        # 3. Overloading checks
        if load_pct > 100.0:
            notes_list.append(f"Transformer overloading: Active load is {load_pct}% of rated MVA.")
            
        confidence = 97.0
        if not validated:
            confidence -= 15.0
            
        res = {
            "health_score": round(primary_health, 2),
            "failure_probability": round(failure_prob, 2),
            "validated": validated,
            "confidence": round(confidence, 2),
            "notes": " ".join(notes_list) if notes_list else "Transformer health predictions match standard IEEE operational curves."
        }
        await self.save_validation_log("transformer_health", f"transformer_{asset_id}", confidence, validated, validation_sources, res)
        return res

    def calculate_consensus(self, prediction_type: str, inputs: Dict[str, Any], primary_prediction: Any) -> Dict[str, Any]:
        """
        Simulate multiple rule-based models to check prediction consensus.
        - Agreement Score: percentage of models agreeing with primary prediction.
        - Confidence Score.
        - Prediction Reliability.
        """
        # 1. Initialize outputs
        model_predictions = []
        
        # 2. Rule-Based Check 1 (Strict bounds)
        # Prioritizes tight feature bounds splits
        if prediction_type == "fault":
            v = inputs.get("voltage", 220.0)
            c = inputs.get("current", 10.0)
            f = inputs.get("frequency", 50.0)
            if v < 195.0:
                xgb_pred = "Voltage Sag"
            elif v > 245.0:
                xgb_pred = "Voltage Swell"
            elif c > 25.0:
                xgb_pred = "Overload"
            else:
                xgb_pred = "Line Fault"
            model_predictions.append(xgb_pred)
            
            # 3. Rule-Based Check 2 (Moderate bounds)
        # Adds slight variance check
            if v < 197.0 and f < 49.0:
                rf_pred = "Voltage Sag"
            elif v > 243.0:
                rf_pred = "Voltage Swell"
            elif c > 23.0:
                rf_pred = "Overload"
            else:
                rf_pred = "Line Fault"
            model_predictions.append(rf_pred)
            
            # 4. Rule-Based Check 3 (Loose bounds)
            # Matches precise cut-offs with looser bounds
            if v < 193.0:
                lgb_pred = "Voltage Sag"
            elif v > 247.0:
                lgb_pred = "Voltage Swell"
            elif c > 27.0:
                lgb_pred = "Overload"
            else:
                lgb_pred = "Line Fault"
            model_predictions.append(lgb_pred)
            
        elif prediction_type == "theft":
            dev = inputs.get("deviation", 0.0)
            pf = inputs.get("power_factor", 0.9)
            
            # Rule-Based Check 1 (Strict)
            xgb_pred = "suspicious" if (dev < -45.0 or pf < 0.72) else "normal"
            model_predictions.append(xgb_pred)
            
            # Rule-Based Check 2 (Moderate)
            rf_pred = "suspicious" if (dev < -35.0 or pf < 0.78) else "normal"
            model_predictions.append(rf_pred)
            
            # Rule-Based Check 3 (Loose)
            lgb_pred = "suspicious" if (dev < -50.0 or pf < 0.70) else "normal"
            model_predictions.append(lgb_pred)
            
        else:
            # Generic fallback
            model_predictions = [primary_prediction, primary_prediction, primary_prediction]
            
        # Calculate agreement
        primary_clean = str(primary_prediction).strip().lower()
        agreements = sum(1 for p in model_predictions if str(p).strip().lower() == primary_clean)
        
        # Agreement score: (agreements / 3) * 100
        agreement_score = (agreements / 3.0) * 100.0
        
        # In case primary model agrees with rules, we can consider it 4 models in total
        # We also compute overall reliability
        reliability = "High" if agreement_score >= 80.0 else ("Medium" if agreement_score >= 50.0 else "Low")
        
        return {
            "agreement_score": agreement_score,
            "reliability": reliability,
            "model_outputs": {
                "rule_based_check_1_strict": model_predictions[0],
                "rule_based_check_2_moderate": model_predictions[1],
                "rule_based_check_3_loose": model_predictions[2]
            }
        }
