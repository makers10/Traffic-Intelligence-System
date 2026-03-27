from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class EventCreate(BaseModel):
    name: str
    event_type: str = Field(..., examples=["concert", "match", "protest", "festival"])
    junction_id: str
    location: Optional[str] = None
    starts_at: datetime
    ends_at: Optional[datetime] = None
    expected_attendance: Optional[int] = Field(None, ge=0)
    impact_radius_km: float = 2.0
    source: str = "manual"


class EventOut(EventCreate):
    id: int
    impact_score: float
    is_active: bool

    class Config:
        from_attributes = True
