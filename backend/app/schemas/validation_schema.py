from pydantic import BaseModel
from typing import List, Dict, Optional, Any

class LoadValidationResponse(BaseModel):
    predicted_demand: float
    confidence: float
    validated: bool
    validation_sources: List[str]
    notes: Optional[str] = None

class RenewableValidationResponse(BaseModel):
    solar_forecast: float
    wind_forecast: float
    confidence: float
    validated: bool
    notes: Optional[str] = None

class FaultValidationResponse(BaseModel):
    fault_type: str
    ml_probability: float
    rule_validation: bool
    confidence: float
    notes: Optional[str] = None

class TheftValidationResponse(BaseModel):
    consumer_id: str
    theft_probability: float
    validated: bool
    confidence: float
    notes: Optional[str] = None

class TransformerValidationResponse(BaseModel):
    health_score: float
    failure_probability: float
    validated: bool
    notes: Optional[str] = None

class ValidationDashboardResponse(BaseModel):
    prediction_confidence: float
    data_quality_score: float
    model_agreement_score: float
    last_validation_time: str
    api_status: Dict[str, str]
    module_status: Dict[str, bool]
