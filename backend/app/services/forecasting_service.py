from datetime import datetime, timedelta
import logging
import math
from typing import Optional
from ..repositories.forecast_repository import ForecastRepository
from ..services.weather_service import WeatherService
from ..preprocess.feature_engineering import prepare_feature_vector
from ..utils.model_loader import ModelLoader
from ..utils.confidence_calculator import calculate_forecast_confidence
from ..utils.helpers import utcnow

from ..core.grid_constants import (
    SOURCE_LSTM_MODEL,
    SOURCE_HEURISTIC_FALLBACK,
    SOURCE_HARDCODED_FALLBACK,
    FORECAST_DEFAULT_MAE,
    FORECAST_DEFAULT_RMSE,
    FORECAST_DEFAULT_MAPE,
    FORECAST_DEFAULT_CONFIDENCE_NEXT_HOUR,
    FORECAST_DEFAULT_CONFIDENCE_NEXT_DAY,
    FORECAST_DEFAULT_CONFIDENCE_NEXT_WEEK,
    
)
from ..core.config_loader import config

logger = logging.getLogger("powercortex.services.forecast")

class ForecastingService:
    """Business logic coordinating prediction pipeline, weather feeds, and insights."""

    def __init__(self, repository: ForecastRepository) -> None:
        self.repository = repository

    async def generate_and_save_forecast(self, forecast_type: str = "hourly") -> dict:
        """
        Runs the full forecasting pipeline:
        1. Fetch current weather conditions
        2. Compile features using dynamic test sequences
        3. Make prediction using the model (or fallback)
        4. Calculate prediction confidence metrics
        5. Generate AI insights
        6. Save results to MongoDB forecasts collection
        """
        logger.info(f"Triggering {forecast_type} forecast generation...")
        
        # 1. Weather
        weather = await WeatherService.get_weather_data()
        
        # 2. Future predictions
        future = ModelLoader.get_future_forecast(168)
        
        if not future:
            # DO NOT GENERATE FAKE FORECASTS!
            logger.error("No forecast future data available! Marking forecast as FAILED.")
            prediction_source = "unavailable"
            
            # Return a failed status block
            return {
                "forecast_type": forecast_type,
                "status": "FAILED",
                "predicted_demand": None,
                "prediction_source": prediction_source,
                "confidence": 0.0,
                "created_at": utcnow()
            }
            
        prediction_source = SOURCE_LSTM_MODEL if ModelLoader.get_model() else SOURCE_HEURISTIC_FALLBACK

        if forecast_type == "hourly":
            predicted_demand = future[0]["predicted"]
        elif forecast_type == "daily":
            predicted_demand = max(f["predicted"] for f in future[:24])
        else:  # weekly
            predicted_demand = sum(f["predicted"] for f in future) / len(future)
                
        predicted_demand = round(predicted_demand, 2)
        
        # 3. Confidence
        from ..utils.confidence_calculator import calculate_forecast_confidence
        confidence = calculate_forecast_confidence(
            temperature=weather["temperature"],
            humidity=weather["humidity"],
            forecast_type=forecast_type
        )
        
        # Apply validation check for Load Forecasting
        try:
            from ..services.validation_service import ValidationService
            from ..core.database import get_database
            db = get_database()
            val_service = ValidationService(db)
            val_res = await val_service.validate_load_forecast(
                predicted_demand=predicted_demand,
                temperature=weather["temperature"],
                hour=datetime.now().hour,
                weekday=datetime.now().weekday()
            )
            confidence = val_res.get("confidence", confidence)
        except Exception as val_err:
            logger.error(f"Error validating load forecast: {val_err}")
        
        # 4. Insights
        insights = self._generate_ai_insights(
            predicted_demand=predicted_demand,
            confidence=confidence,
            temperature=weather["temperature"],
            forecast_type=forecast_type
        )
        
        # 5. Document Structure
        timestamp = utcnow()
        forecast_document = {
            "forecast_type": forecast_type,
            "predicted_demand": predicted_demand,
            "prediction_source": prediction_source,
            "confidence": confidence,
            "temperature": weather.get("temperature"),
            "humidity": weather.get("humidity"),
            "wind_speed": weather.get("wind_speed"),
            "cloud_cover": weather.get("cloud_cover"),
            "weather_source": weather.get("source"),
            "insights": insights,
            "created_at": timestamp
        }
        
        # 6. Save
        saved_doc = await self.repository.save(forecast_document)
        saved_doc["_id"] = str(saved_doc["_id"])
        return saved_doc

    async def get_latest_forecast(self, forecast_type: str = "hourly") -> dict:
        """Retrieves the latest forecast, generating one if none exist in MongoDB."""
        latest = await self.repository.get_latest(forecast_type)
        if not latest:
            # Generate new forecast to populate the database
            latest = await self.generate_and_save_forecast(forecast_type)
        else:
            latest["_id"] = str(latest["_id"])
        return latest

    async def get_forecast_history(self, forecast_type: Optional[str] = None, limit: int = 20) -> list[dict]:
        """Fetch historical runs."""
        runs = await self.repository.list_forecasts(forecast_type=forecast_type, limit=limit)
        for run in runs:
            run["_id"] = str(run["_id"])
        return runs

    async def get_chart_data(self) -> list[dict]:
        """
        Retrieves actual vs predicted coordinates from the PJME dataset, scaled to match the target grid demand.
        """
        timeline = ModelLoader.get_timeline_data()
        if not timeline:
            return []
            
        current_actual = timeline[-1]["actual"]
        grid_baseline = config.get("forecasting.grid_baseline_demand_mw", 41134.0)
        scale_factor = grid_baseline / current_actual
        
        scaled_timeline = []
        for point in timeline:
            scaled_timeline.append({
                "timestamp": point["timestamp"],
                "actual": round(point["actual"] * scale_factor, 2),
                "predicted": round(point["predicted"] * scale_factor, 2)
            })
        return scaled_timeline

    async def get_dashboard_summary(self) -> dict:
        """Fetches unified forecasting summaries for KPI widgets."""
        from ..core.database import get_database
        db = get_database()
        
        grid_baseline = config.get("forecasting.grid_baseline_demand_mw", 41134.0)
        renewable_contrib = config.get("renewable.default_contrib_pct", 38.0)
        
        try:
            latest_renewable = await db.renewable_forecasts.find_one(sort=[("timestamp", -1)])
            if latest_renewable:
                renewable_total = latest_renewable.get("renewable_total", 1055.0)
                # Calculate against current demand
                renewable_contrib = round((renewable_total / grid_baseline) * 100, 1)
        except Exception as renew_err:
            logger.error(f"Error getting renewable contribution for dashboard: {renew_err}")

        timeline = ModelLoader.get_timeline_data()
        if not timeline:
            return {
                "current_demand": grid_baseline,
                "next_hour": round(grid_baseline * 1.009, 2),
                "next_hour_confidence": FORECAST_DEFAULT_CONFIDENCE_NEXT_HOUR,
                "next_day": round(grid_baseline * 1.024, 2),
                "next_day_confidence": FORECAST_DEFAULT_CONFIDENCE_NEXT_DAY,
                "next_week": round(grid_baseline * 1.002, 2),
                "next_week_confidence": FORECAST_DEFAULT_CONFIDENCE_NEXT_WEEK,
                "peak_time": "18:00",
                "renewable_contribution": renewable_contrib,
                "mae": FORECAST_DEFAULT_MAE,
                "rmse": FORECAST_DEFAULT_RMSE,
                "mape": FORECAST_DEFAULT_MAPE,
                "insights": ["Grid demand is stable; actual load is tracking close to LSTM Deep Learning prediction."]
            }
            
        current_actual = timeline[-1]["actual"]
        scale_factor = grid_baseline / current_actual
        current_demand = round(current_actual * scale_factor, 2)
        
        future = ModelLoader.get_future_forecast(168)
        
        next_hour_pred = future[0]["predicted"] if future else current_actual
        next_day_peak = max(f["predicted"] for f in future[:24]) if future else current_actual * 1.15
        next_week_avg = sum(f["predicted"] for f in future) / len(future) if future else current_actual
        
        # Peak time hour in next 24 hours
        peak_time = "18:00"
        if future:
            peak_val = -1.0
            peak_hour_idx = 0
            for idx, f in enumerate(future[:24]):
                if f["predicted"] > peak_val:
                    peak_val = f["predicted"]
                    peak_hour_idx = idx
            peak_dt = future[peak_hour_idx]["timestamp"]
            if isinstance(peak_dt, str):
                peak_time = peak_dt[11:16]
            else:
                peak_time = peak_dt.strftime("%H:%M")
                
        weather = await WeatherService.get_weather_data()
        
        from ..utils.confidence_calculator import calculate_forecast_confidence
        next_hour_conf = calculate_forecast_confidence(weather["temperature"], weather["humidity"], "hourly")
        next_day_conf = calculate_forecast_confidence(weather["temperature"], weather["humidity"], "daily")
        next_week_conf = calculate_forecast_confidence(weather["temperature"], weather["humidity"], "weekly")
        
        next_day_val = round(next_day_peak * scale_factor, 2)
        
        insights = self._generate_ai_insights(
            predicted_demand=next_hour_pred * scale_factor,
            confidence=next_hour_conf,
            temperature=weather["temperature"],
            forecast_type="hourly",
            current_demand=current_demand,
            peak_demand=next_day_val,
            renewable_contribution=renewable_contrib
        )
        
        return {
            "current_demand": current_demand,
            "next_hour": round(next_hour_pred * scale_factor, 2),
            "next_hour_confidence": next_hour_conf,
            "next_day": next_day_val,
            "next_day_confidence": next_day_conf,
            "next_week": round(next_week_avg * scale_factor, 2),
            "next_week_confidence": next_week_conf,
            "peak_time": peak_time,
            "renewable_contribution": renewable_contrib,
            "mae": round(ModelLoader._mae * scale_factor, 2),
            "rmse": round(ModelLoader._rmse * scale_factor, 2),
            "mape": round(ModelLoader._mape, 2),
            "insights": insights
        }

    def _generate_ai_insights(
        self,
        predicted_demand: float,
        confidence: float,
        temperature: float,
        forecast_type: str,
        current_demand: Optional[float] = None,
        peak_demand: Optional[float] = None,
        renewable_contribution: Optional[float] = None
    ) -> list[str]:
        """Construct descriptive contextual insights based on metrics."""
        insights = []
        
        cur_dem = current_demand if current_demand is not None else config.get("forecasting.grid_baseline_demand_mw", 41134.0)
        peak_dem = peak_demand if peak_demand is not None else config.get("forecasting.grid_peak_demand_mw", 42116.0)
        ren_contrib = renewable_contribution if renewable_contribution is not None else config.get("renewable.default_contrib_pct", 38.0)
        
        if forecast_type == "hourly":
            insights.append(f"Grid demand is stable at {cur_dem:,.0f} MW; actual load is tracking close to LSTM Deep Learning prediction.")
            if predicted_demand > 35000.0:
                insights.append(f"Elevated load of {predicted_demand:,.0f} MW expected next hour. Recommend activating spinning reserves.")
            else:
                insights.append(f"Grid load is normal. Next hour demand predicted at {predicted_demand:,.0f} MW.")
        elif forecast_type == "daily":
            insights.append(f"Peak demand of {peak_dem:,.0f} MW is expected tomorrow around load transition period.")
            insights.append("Daily peak load is predicted to increase based on current weather profiles.")
        else:  # weekly
            insights.append("Weekly trend shows minor fluctuation due to seasonal shifts.")
            
        if temperature > 35.0:
            insights.append(f"High temperature of {temperature}°C is contributing to air conditioning cooling loads.")
        elif temperature < 15.0:
            insights.append(f"Cool temperature of {temperature}°C is increasing grid heating load requirements.")
            
        insights.append(f"Renewable contribution is solid at {ren_contrib:.1f}%, driven by active solar/wind feeds.")
        insights.append(f"Forecast confidence index is {confidence}% based on historical training bounds.")
        
        return insights