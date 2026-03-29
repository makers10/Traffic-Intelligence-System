from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.sql import func
from app.db import Base


class TransportReading(Base):
    """Rideshare and public transit volume readings per junction/zone."""
    __tablename__ = "transport_readings"

    id = Column(Integer, primary_key=True, index=True)
    junction_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Rideshare
    rideshare_trips = Column(Integer, default=0)   # Uber/Ola/Rapido trips
    rideshare_avg_wait_min = Column(Float)          # avg pickup wait time

    # Public transit
    metro_boardings = Column(Integer, default=0)
    bus_boardings = Column(Integer, default=0)

    # Derived
    road_pressure_index = Column(Float)  # 0-1, higher = more cars on road
    transit_shift_score = Column(Float)  # 0-1, higher = more people using transit
