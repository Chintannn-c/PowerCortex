import httpx
import logging
from datetime import datetime, timezone
from typing import Optional
from ..core.config import settings
from ..core.grid_constants import (
    WEATHER_CACHE_DURATION_SECONDS,
    SOURCE_OPENWEATHERMAP,
    SOURCE_WEATHER_UNAVAILABLE,
)

logger = logging.getLogger("powercortex.services.weather")

class WeatherService:
    """Fetches real-time weather data from OpenWeatherMap. Returns an error
    response instead of fake data when the API is unavailable."""
    
    # Simple in-memory cache to prevent hitting rate limits
    _cache = {}
    _cache_duration_seconds = WEATHER_CACHE_DURATION_SECONDS

    @classmethod
    async def get_weather_data(
        cls, 
        city: Optional[str] = None, 
        latitude: float = None, 
        longitude: float = None
    ) -> dict:
        """
        Fetches current weather for the grid location.
        Supports query by city name or by coordinates.
        Returns a dict with weather data and a ``source`` field.
        When the API is unavailable the ``source`` will be ``"unavailable"``.
        """
        # Apply defaults from settings
        if latitude is None:
            latitude = settings.DEFAULT_LATITUDE
        if longitude is None:
            longitude = settings.DEFAULT_LONGITUDE
        if city is None:
            city = settings.DEFAULT_CITY

        if city:
            cache_key = city.lower().strip()
        else:
            cache_key = f"{round(latitude, 2)}_{round(longitude, 2)}"
            
        now = datetime.now(timezone.utc)
        
        # Check cache
        if cache_key in cls._cache:
            cached_data, cached_time = cls._cache[cache_key]
            if (now - cached_time).total_seconds() < cls._cache_duration_seconds:
                # Only return cached data if it was a successful API response
                if cached_data.get("source") != SOURCE_WEATHER_UNAVAILABLE:
                    logger.info(f"Returning cached weather data for key: {cache_key}")
                    return cached_data

        api_key = getattr(settings, "OPENWEATHER_API_KEY", None)
        if api_key and api_key != "YOUR_OPENWEATHER_KEY":
            try:
                if city:
                    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
                else:
                    url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={api_key}&units=metric"
                
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(url)
                    if response.status_code == 200:
                        data = response.json()
                        weather_data = {
                            "temperature": float(data["main"]["temp"]),
                            "humidity": int(data["main"]["humidity"]),
                            "wind_speed": float(data["wind"]["speed"]),
                            "cloud_cover": int(data["clouds"]["all"]),
                            "source": SOURCE_OPENWEATHERMAP,
                            "data_source": SOURCE_OPENWEATHERMAP,
                            "city": data.get("name", city or settings.DEFAULT_CITY)
                        }
                        cls._cache[cache_key] = (weather_data, now)
                        logger.info(f"Successfully fetched weather from OpenWeatherMap for {cache_key}.")
                        return weather_data
                    else:
                        logger.warning(
                            "OpenWeatherMap API returned status code %d for key %s.",
                            response.status_code, cache_key
                        )
            except Exception:
                logger.exception("Failed to fetch weather from OpenWeatherMap for key %s.", cache_key)

        # ── No mock data — return an explicit "unavailable" response ──
        logger.warning("Weather data unavailable for %s. API key missing or request failed.", cache_key)
        return {
            "temperature": None,
            "humidity": None,
            "wind_speed": None,
            "cloud_cover": None,
            "source": SOURCE_WEATHER_UNAVAILABLE,
            "data_source": SOURCE_WEATHER_UNAVAILABLE,
            "city": city or settings.DEFAULT_CITY,
            "error": "Weather API is not configured or is temporarily unavailable."
        }
