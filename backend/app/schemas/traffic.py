from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# --- Ingest ---
class TrafficReadingCreate(BaseModel):
    junction_id: str
    speed_kmh: float = Field(..., ge=0, le=300)
    vehicle_density: int = Field(..., ge=0)
    occupancy_pct: Optional[float] = Field(None, ge=0, le=100)
    weather_condition: Optional[str] = None
    temperature: Optional[float] = None
    visibility_m: Optional[float] = None

class TrafficReadingOut(TrafficReadingCreate):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# --- Prediction ---
class PredictionRequest(BaseModel):
    junction_id: str
    horizon_minutes: int = Field(30, ge=5, le=120)

class PredictionOut(BaseModel):
    junction_id: str
    forecast_time: datetime
    congestion_level: float = Field(..., ge=0, le=1)
    predicted_speed: Optional[float]
    confidence: float
    label: str  # free / moderate / heavy / standstill

    class Config:
        from_attributes = True

# --- Accident ---
class AccidentAlertOut(BaseModel):
    id: int
    junction_id: str
    detected_at: datetime
    severity: str
    speed_drop_pct: Optional[float]
    density_spike_pct: Optional[float]
    is_confirmed: bool

    class Config:
        from_attributes = True
