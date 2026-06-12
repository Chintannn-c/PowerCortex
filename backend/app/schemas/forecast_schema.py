from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List

class ForecastInfo(BaseModel):
    predicted_demand: float = Field(..., description="Predicted electricity load in Megawatts (MW)")
    unit: str = "MW"
    confidence: float = Field(..., description="Confidence percentage score of the forecast")

class ForecastResponse(BaseModel):
    success: bool = True
    forecast: ForecastInfo

class ForecastDocumentResponse(BaseModel):
    id: str = Field(..., alias="_id")
    forecast_type: str
    predicted_demand: float
    confidence: float
    temperature: float
    humidity: int
    wind_speed: float
    cloud_cover: int
    insights: list[str]
    created_at: datetime

    model_config = ConfigDict(populate_by_name=True)

class ForecastListResponse(BaseModel):
    success: bool = True
    data: list[ForecastDocumentResponse]

class ForecastGenerateRequest(BaseModel):
    forecast_type: str = Field("hourly", description="Type of forecast (hourly, daily, weekly)")

class ChartPoint(BaseModel):
    timestamp: str
    actual: float
    predicted: float

class ChartDataResponse(BaseModel):
    success: bool = True
    data: list[ChartPoint]

class DashboardSummaryResponse(BaseModel):
    success: bool = True
    current_demand: float
    next_hour: float
    next_hour_confidence: float
    next_day: float
    next_day_confidence: float
    next_week: float
    next_week_confidence: float
    peak_time: str
    renewable_contribution: float
    mae: float
    rmse: float
    mape: float
    insights: list[str]
