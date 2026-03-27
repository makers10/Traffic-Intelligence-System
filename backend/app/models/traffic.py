from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from app.db import Base

class TrafficReading(Base):
    """Raw traffic sensor readings per junction/segment."""
    __tablename__ = "traffic_readings"

    id = Column(Integer, primary_key=True, index=True)
    junction_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    speed_kmh = Column(Float, nullable=False)          # avg vehicle speed
    vehicle_density = Column(Integer, nullable=False)  # vehicles per km
    occupancy_pct = Column(Float)                      # road occupancy %
    weather_condition = Column(String)                 # clear/rain/fog/etc
    temperature = Column(Float)
    visibility_m = Column(Float)
    raw_data = Column(JSON)                            # extra sensor payload


class CongestionPrediction(Base):
    """Stored predictions for future congestion levels."""
    __tablename__ = "congestion_predictions"

    id = Column(Integer, primary_key=True, index=True)
    junction_id = Column(String, index=True, nullable=False)
    predicted_at = Column(DateTime(timezone=True), server_default=func.now())
    forecast_time = Column(DateTime(timezone=True), nullable=False, index=True)
    congestion_level = Column(Float, nullable=False)   # 0.0 - 1.0
    predicted_speed = Column(Float)
    confidence = Column(Float)
    model_version = Column(String, default="v1")


class AccidentAlert(Base):
    """Detected anomalies flagged as potential accidents."""
    __tablename__ = "accident_alerts"

    id = Column(Integer, primary_key=True, index=True)
    junction_id = Column(String, index=True, nullable=False)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    severity = Column(String, nullable=False)          # low/medium/high
    speed_drop_pct = Column(Float)                     # % drop from baseline
    density_spike_pct = Column(Float)                  # % spike from baseline
    is_confirmed = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True))
    notes = Column(String)
