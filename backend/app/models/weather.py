from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.sql import func
from app.db import Base


class WeatherSnapshot(Base):
    """Cached weather data per location/junction."""
    __tablename__ = "weather_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    junction_id = Column(String, index=True, nullable=False)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    condition = Column(String)        # clear/rain/fog/snow/etc
    temperature = Column(Float)
    humidity = Column(Float)
    wind_speed = Column(Float)
    visibility_m = Column(Float)
    precipitation_mm = Column(Float)
    impact_score = Column(Float)      # 0.0 (no impact) - 1.0 (severe)
