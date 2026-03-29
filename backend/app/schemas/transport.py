from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class TransportReadingCreate(BaseModel):
    junction_id: str
    rideshare_trips: int = Field(0, ge=0)
    rideshare_avg_wait_min: Optional[float] = None
    metro_boardings: int = Field(0, ge=0)
    bus_boardings: int = Field(0, ge=0)


class TransportReadingOut(TransportReadingCreate):
    id: int
    timestamp: datetime
    road_pressure_index: Optional[float]
    transit_shift_score: Optional[float]
    insight: str

    class Config:
        from_attributes = True


class TransportInsightOut(BaseModel):
    junction_id: str
    period_hours: int
    avg_rideshare_trips: float
    avg_metro_boardings: float
    avg_bus_boardings: float
    avg_road_pressure: float
    avg_transit_shift: float
    recommendation: str
