import os
import logging
from datetime import timedelta
import requests
from bson import ObjectId

from ..core.database import get_database
from ..core.config import settings
from ..core.grid_constants import (
    SOURCE_WEATHER_UNAVAILABLE,
    FORECAST_CACHE_DURATION_MINUTES,
)
from ..ml.renewable_predictor import RenewablePredictor
from ..utils.helpers import utcnow
from ..models.notification import NotificationCreate
from ..services.notification_service import NotificationService

logger = logging.getLogger("powercortex.services.renewable_service")

class RenewableService:
    @staticmethod
    async def get_current_weather(city: str = None) -> dict:
        """
        Fetches current weather data from WeatherService with a 10-minute database cache.
        """
        if city is None:
            city = settings.DEFAULT_CITY

        db = get_database()
        
        # Check cache in MongoDB (weather_data collection)
        cache_threshold = utcnow() - timedelta(minutes=FORECAST_CACHE_DURATION_MINUTES)
        cached_data = await db.weather_data.find_one(
            {"city": city, "timestamp": {"$gte": cache_threshold}}
        )
        
        if cached_data:
            # Only use cache if it was a successful fetch, not an unavailable marker
            if cached_data.get("status") != "weather_unavailable":
                logger.debug("Returning cached weather data from MongoDB.")
                cached_data["_id"] = str(cached_data["_id"])
                return cached_data

        from ..services.weather_service import WeatherService
        weather = await WeatherService.get_weather_data(city=city)
        
        is_unavailable = weather.get("source") == SOURCE_WEATHER_UNAVAILABLE

        weather_record = {
            "timestamp": utcnow(),
            "city": city,
            "temperature": weather["temperature"],
            "humidity": weather["humidity"],
            "wind_speed": weather["wind_speed"],
            "cloud_cover": weather["cloud_cover"],
            "data_source": weather.get("data_source", "unknown"),
            "status": "weather_unavailable" if is_unavailable else "success",
        }
        
        result = await db.weather_data.insert_one(weather_record)
        weather_record["_id"] = str(result.inserted_id)
        return weather_record

    @staticmethod
    async def predict_renewables(temp: float, humidity: float, wind_speed: float, cloud_cover: float, city: str = "ahmedabad") -> dict:
        """
        Runs ML models to predict solar and wind generation, saves results in MongoDB, and triggers alert notifications if there's a >25% drop.
        """
        db = get_database()
        
        solar_gen, wind_gen, prediction_source = RenewablePredictor.predict_renewables(temp, humidity, wind_speed, cloud_cover, city)
        
        # Validate forecast predictions using engineering/weather rules
        try:
            from ..services.validation_service import ValidationService
            val_service = ValidationService(db)
            val_res = await val_service.validate_renewable_forecast(
                solar_forecast=solar_gen,
                wind_forecast=wind_gen,
                temp=temp,
                humidity=humidity,
                wind_speed=wind_speed,
                cloud_cover=cloud_cover
            )
            solar_gen = val_res.get("solar_forecast", solar_gen)
            wind_gen = val_res.get("wind_forecast", wind_gen)
        except Exception:
            logger.exception("Error validating renewable predictions.")

        total_gen = round(solar_gen + wind_gen, 1)
        now = utcnow()

        # Check for alert (drops > 25% compared to the latest historical forecast in MongoDB)
        try:
            latest = await db.renewable_forecasts.find_one(
                sort=[("timestamp", -1)]
            )
            if latest:
                last_solar = latest.get("solar_generation", 0.0)
                last_wind = latest.get("wind_generation", 0.0)

                if last_solar > 0:
                    solar_drop = (last_solar - solar_gen) / last_solar
                    if solar_drop > 0.25:
                        drop_pct = int(solar_drop * 100)
                        notif = NotificationCreate(
                            title="Renewable Output Drop",
                            message=f"Solar generation decreased by {drop_pct}% (from {last_solar} MW to {solar_gen} MW)",
                            type="renewable_alert",
                            screen="forecasting"
                        )
                        await NotificationService.create_and_send_notification(notif)
                        logger.info("Triggered solar drop notification: %d%% decrease.", drop_pct)

                if last_wind > 0:
                    wind_drop = (last_wind - wind_gen) / last_wind
                    if wind_drop > 0.25:
                        drop_pct = int(wind_drop * 100)
                        notif = NotificationCreate(
                            title="Renewable Output Drop",
                            message=f"Wind generation decreased by {drop_pct}% (from {last_wind} MW to {wind_gen} MW)",
                            type="renewable_alert",
                            screen="forecasting"
                        )
                        await NotificationService.create_and_send_notification(notif)
                        logger.info("Triggered wind drop notification: %d%% decrease.", drop_pct)
        except Exception:
            logger.exception("Error checking renewable drop alerts.")

        # Save forecast to MongoDB
        forecast_record = {
            "timestamp": now,
            "temperature": temp,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "cloud_cover": cloud_cover,
            "solar_generation": solar_gen,
            "wind_generation": wind_gen,
            "renewable_total": total_gen,
            "prediction_source": prediction_source,
            "city": city
        }
        
        result = await db.renewable_forecasts.insert_one(forecast_record)
        forecast_record["_id"] = str(result.inserted_id)
        
        return forecast_record

    @staticmethod
    async def get_current_forecast(city: str = None) -> dict:
        """
        Retrieves the latest prediction, or runs a live prediction using current weather conditions.
        """
        if city is None:
            city = settings.DEFAULT_CITY

        db = get_database()
        
        # Check if we have a recent prediction (less than 10 mins old)
        cache_threshold = utcnow() - timedelta(minutes=FORECAST_CACHE_DURATION_MINUTES)
        latest = await db.renewable_forecasts.find_one(
            {"timestamp": {"$gte": cache_threshold}},
            sort=[("timestamp", -1)]
        )
        
        if latest:
            latest["_id"] = str(latest["_id"])
            return latest

        # Otherwise, fetch weather and run forecast
        weather = await RenewableService.get_current_weather(city)

        # If weather is unavailable, we cannot produce a valid forecast
        if weather.get("status") == "weather_unavailable":
            logger.warning("Cannot produce renewable forecast: weather data unavailable.")
            return {
                "solar_generation": None,
                "wind_generation": None,
                "renewable_total": None,
                "timestamp": utcnow(),
                "prediction_source": SOURCE_WEATHER_UNAVAILABLE,
                "error": "Weather data unavailable — renewable forecast cannot be generated.",
            }

        forecast = await RenewableService.predict_renewables(
            temp=weather["temperature"],
            humidity=weather["humidity"],
            wind_speed=weather["wind_speed"],
            cloud_cover=weather["cloud_cover"]
        )
        return forecast

    @staticmethod
    async def get_forecast_history(limit: int = 24) -> list:
        """
        Retrieves stored forecasts from MongoDB.
        """
        db = get_database()
        cursor = db.renewable_forecasts.find().sort("timestamp", -1).limit(limit)
        history = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            history.append(doc)
        return history
