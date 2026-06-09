from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime

from ..services.renewable_service import RenewableService
from ..core.dependencies import get_current_user
from ..core.config import settings
from ..models.user import UserDocument

router = APIRouter(prefix="/api/v1/renewables", tags=["Renewables"])

class PredictionRequest(BaseModel):
    temperature: float = Field(..., description="Temperature in Celsius")
    humidity: float = Field(..., description="Humidity percentage")
    wind_speed: float = Field(..., description="Wind speed in m/s")
    cloud_cover: float = Field(..., description="Cloud cover percentage")

class PredictionResponse(BaseModel):
    solar_generation: float
    wind_generation: float
    renewable_total: float
    prediction_time: Optional[datetime] = None

@router.get("/current")
async def get_current_forecast(city: Optional[str] = None, current_user: UserDocument = Depends(get_current_user)):
    """
    Retrieve the current renewable forecast based on live/cached weather conditions.
    """
    try:
        forecast = await RenewableService.get_current_forecast(city or settings.DEFAULT_CITY)
        return {
            "solar_generation": forecast["solar_generation"],
            "wind_generation": forecast["wind_generation"],
            "renewable_total": forecast["renewable_total"],
            "timestamp": forecast["timestamp"].isoformat() if isinstance(forecast["timestamp"], datetime) else forecast["timestamp"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch current forecast: {str(e)}"
        )

@router.post("/predict")
async def predict_forecast(req: PredictionRequest, current_user: UserDocument = Depends(get_current_user)):
    """
    Execute DL (Keras) model prediction using custom telemetry inputs and save result in MongoDB.
    """
    try:
        forecast = await RenewableService.predict_renewables(
            temp=req.temperature,
            humidity=req.humidity,
            wind_speed=req.wind_speed,
            cloud_cover=req.cloud_cover
        )
        return {
            "solar_generation": forecast["solar_generation"],
            "wind_generation": forecast["wind_generation"],
            "renewable_total": forecast["renewable_total"],
            "timestamp": forecast["timestamp"].isoformat() if isinstance(forecast["timestamp"], datetime) else forecast["timestamp"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ML prediction execution failed: {str(e)}"
        )

@router.get("/history")
async def get_historical_forecasts(limit: int = 24, current_user: UserDocument = Depends(get_current_user)):
    """
    Retrieve historical stored forecasts from MongoDB.
    """
    try:
        history = await RenewableService.get_forecast_history(limit)
        return {
            "success": True,
            "data": history
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve forecast history: {str(e)}"
        )
