from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.db import Base


class TrafficEvent(Base):
    """Large gatherings or incidents that affect traffic flow."""
    __tablename__ = "traffic_events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    event_type = Column(String, nullable=False)   # concert/match/protest/festival
    junction_id = Column(String, index=True)      # nearest affected junction
    location = Column(String)
    starts_at = Column(DateTime(timezone=True), nullable=False, index=True)
    ends_at = Column(DateTime(timezone=True))
    expected_attendance = Column(Integer)
    impact_radius_km = Column(Float, default=2.0)
    impact_score = Column(Float)                  # 0.0 - 1.0
    is_active = Column(Boolean, default=True)
    source = Column(String, default="manual")     # manual/api
