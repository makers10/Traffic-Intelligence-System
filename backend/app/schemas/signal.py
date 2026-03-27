from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class SignalPhase(BaseModel):
    direction: str
    green_s: int
    red_s: int


class SignalOptimizeRequest(BaseModel):
    junction_id: str
    congestion_level: Optional[float] = Field(None, ge=0.0, le=1.0)


class SignalPlanOut(BaseModel):
    junction_id: str
    congestion_level: float
    green_duration_s: int
    red_duration_s: int
    cycle_time_s: int
    phases: List[SignalPhase]
    reason: str
    generated_at: Optional[datetime]

    class Config:
        from_attributes = True
