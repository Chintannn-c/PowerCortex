from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from ..utils.helpers import utcnow


class NotificationCreate(BaseModel):
    title: str = Field(..., max_length=150)
    message: str = Field(..., max_length=500)
    type: str = Field(..., description="e.g., asset, forecast, fault, ai, report")
    screen: str = Field(..., description="Screen route/identifier to open on tap")
    entity_id: Optional[str] = Field(default=None, description="ID of the asset/fault for deep linking")
    user_id: Optional[str] = Field(default=None, description="Target user ID. If None, it's a global broadcast.")


class NotificationResponse(NotificationCreate):
    id: str = Field(alias="_id")
    is_read: bool = Field(default=False)
    created_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}
