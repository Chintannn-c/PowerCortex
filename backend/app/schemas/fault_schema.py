from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List, Optional

class FaultPredictRequest(BaseModel):
    voltage: float = Field(..., json_schema_extra={"example": 185.0})
    current: float = Field(..., json_schema_extra={"example": 450.0})
    frequency: float = Field(..., json_schema_extra={"example": 49.1})
    asset_name: Optional[str] = Field(default="Transmission Line TL-22A", json_schema_extra={"example": "Transmission Line TL-22A"})

class FaultPredictResponse(BaseModel):
    fault_type: str = Field(..., json_schema_extra={"example": "Voltage Sag"})
    severity: str = Field(..., json_schema_extra={"example": "Critical"})
    probability: float = Field(..., json_schema_extra={"example": 94.2})
    status: str = Field(..., json_schema_extra={"example": "Active"})

class FaultResponse(BaseModel):
    id: str = Field(..., alias="_id")
    fault_id: str
    fault_type: str
    asset_name: str
    severity: str
    probability: float
    status: str
    voltage: float
    current: float
    frequency: float
    detected_at: datetime

    model_config = ConfigDict(populate_by_name=True)

class FaultDashboardResponse(BaseModel):
    active_faults: int
    resolved_today: int
    critical: int
    high: int
    medium: int
    low: int

class FaultAnomalyItem(BaseModel):
    fault_type: str
    asset: str = Field(..., alias="asset_name")
    severity: str
    probability: float

    model_config = ConfigDict(populate_by_name=True)

class FaultAnomaliesResponse(BaseModel):
    active_faults: int
    resolved_today: int
    faults: List[FaultAnomalyItem]

class FaultTimelineItem(BaseModel):
    date: str
    count: int

class FaultListResponse(BaseModel):
    success: bool
    data: List[FaultResponse]
