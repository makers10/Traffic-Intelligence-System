from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas.weather import WeatherOut, WeatherRequest
from app.services import weather_service

router = APIRouter(prefix="/api/v1/weather", tags=["weather"])


@router.post("", response_model=WeatherOut)
async def get_weather(payload: WeatherRequest, db: Session = Depends(get_db)):
    """Fetch weather for a junction location and return traffic impact analysis."""
    return await weather_service.fetch_weather(payload.junction_id, payload.lat, payload.lon, db)
