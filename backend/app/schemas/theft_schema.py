from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class TheftPredictRequest(BaseModel):
    consumer_id: str = Field(..., example="CN-88029")
    current_consumption: float = Field(..., example=420.0)
    avg_consumption: float = Field(..., example=1180.0)
    power_factor: float = Field(..., example=0.72)

class TheftPredictData(BaseModel):
    consumer_id: str
    theft_probability: float
    risk_level: str
    deviation_percentage: float

class TheftPredictResponse(BaseModel):
    success: bool
    data: TheftPredictData

class TheftSuspiciousItem(BaseModel):
    consumer_id: str
    risk_level: str
    theft_probability: float
    sector: Optional[str] = None
    city: Optional[str] = None
    deviation_percentage: Optional[float] = None

class TheftDashboardResponse(BaseModel):
    suspicious_count: int
    high_risk_count: int
    resolved_count: int
    average_probability: float

class ConsumerInvestigationResponse(BaseModel):
    consumer_id: str
    consumer_name: str
    sector: str
    city: str
    current_consumption: float
    avg_consumption: float
    power_factor: float
    monthly_usage: List[float]
    theft_probability: float
    risk_level: str
    deviation_percentage: float
    is_suspicious: bool
    ai_explanation: str
    investigation_notes: str

class TheftDistributionItem(BaseModel):
    name: str  # e.g., "High Risk", "Medium Risk", etc.
    value: int  # count

class TheftTrendPoint(BaseModel):
    month: str  # e.g., "Jan", "Feb" or "Month 1"
    actual: float
    expected: float
