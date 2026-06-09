from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class FaultPredictRequest(BaseModel):
    voltage: float = Field(..., example=185.0)
    current: float = Field(..., example=450.0)
    frequency: float = Field(..., example=49.1)
    asset_name: Optional[str] = Field(default="Transmission Line TL-22A", example="Transmission Line TL-22A")

class FaultPredictResponse(BaseModel):
    fault_type: str = Field(..., example="Voltage Sag")
    severity: str = Field(..., example="Critical")
    probability: float = Field(..., example=94.2)
    status: str = Field(..., example="Active")

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

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

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

    class Config:
        populate_by_name = True

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
