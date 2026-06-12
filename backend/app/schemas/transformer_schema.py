from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List

class TransformerPredictRequest(BaseModel):
    temperature: float = Field(..., json_schema_extra={"example": 67.0})
    voltage: float = Field(..., json_schema_extra={"example": 11.2})
    current: float = Field(..., json_schema_extra={"example": 320.0})
    oil_level: float = Field(..., json_schema_extra={"example": 84.0})
    load_percentage: float = Field(..., json_schema_extra={"example": 72.0})

class TransformerPredictResponse(BaseModel):
    health_score: float = Field(..., json_schema_extra={"example": 92.0})
    risk_score: float = Field(..., json_schema_extra={"example": 8.0})
    failure_probability: float = Field(..., json_schema_extra={"example": 3.0})
    status: str = Field(..., json_schema_extra={"example": "Healthy"})

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

    model_config = ConfigDict(populate_by_name=True)

class TransformerDashboardResponse(BaseModel):
    total: int
    healthy: int
    warning: int
    critical: int

class TransformerListResponse(BaseModel):
    success: bool
    data: List[TransformerResponse]
