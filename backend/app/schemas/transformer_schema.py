from pydantic import BaseModel, Field
from datetime import datetime
from typing import List

class TransformerPredictRequest(BaseModel):
    temperature: float = Field(..., example=67.0)
    voltage: float = Field(..., example=11.2)
    current: float = Field(..., example=320.0)
    oil_level: float = Field(..., example=84.0)
    load_percentage: float = Field(..., example=72.0)

class TransformerPredictResponse(BaseModel):
    health_score: float = Field(..., example=92.0)
    risk_score: float = Field(..., example=8.0)
    failure_probability: float = Field(..., example=3.0)
    status: str = Field(..., example="Healthy")

class TransformerResponse(BaseModel):
    id: str = Field(..., alias="_id")
    asset_id: str
    name: str
    type: str  # e.g., "Distribution Transformer", "11kV Feeder"
    temperature: float
    voltage: float
    current: float
    oil_level: float
    load_percentage: float
    health_score: float
    risk_score: float
    failure_probability: float
    status: str
    last_updated: datetime

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class TransformerDashboardResponse(BaseModel):
    total: int
    healthy: int
    warning: int
    critical: int

class TransformerListResponse(BaseModel):
    success: bool
    data: List[TransformerResponse]
