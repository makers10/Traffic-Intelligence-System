from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class WeatherOut(BaseModel):
    junction_id: str
    condition: str
    temperature: Optional[float]
    humidity: Optional[float]
    wind_speed: Optional[float]
    visibility_m: Optional[float]
    precipitation_mm: Optional[float]
    impact_score: float
    fetched_at: Optional[datetime]
    explanation: str

    class Config:
        from_attributes = True


class WeatherRequest(BaseModel):
    junction_id: str
    lat: float
    lon: float
