from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from ..services.weather_service import WeatherService
from ..core.dependencies import get_current_user
from ..core.config import settings

router = APIRouter(prefix="/api/v1/weather", tags=["Weather"])

@router.get("/current", summary="Get current weather data for a city")
async def get_current_weather(
    city: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Returns current weather conditions from OpenWeatherMap API (with 10-minute cache)
    or realistic mock data if the API key is not configured.
    """
    try:
        weather = await WeatherService.get_weather_data(city=city or settings.DEFAULT_CITY)
        return {
            "success": True,
            "temperature": weather["temperature"],
            "humidity": weather["humidity"],
            "wind_speed": weather["wind_speed"],
            "cloud_cover": weather["cloud_cover"],
            "source": weather.get("source", "Unknown"),
            "city": weather.get("city", city),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch weather data: {str(e)}"
        )
