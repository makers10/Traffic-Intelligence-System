from sqlalchemy import Column, Integer, Float, String, DateTime, JSON
from sqlalchemy.sql import func
from app.db import Base


class SignalPlan(Base):
    """Optimized signal timing suggestions per junction."""
    __tablename__ = "signal_plans"

    id = Column(Integer, primary_key=True, index=True)
    junction_id = Column(String, index=True, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    congestion_level = Column(Float)
    green_duration_s = Column(Integer)    # suggested green phase seconds
    red_duration_s = Column(Integer)
    cycle_time_s = Column(Integer)        # total cycle
    phases = Column(JSON)                 # per-direction phase breakdown
    reason = Column(String)               # human-readable explanation
    applied_at = Column(DateTime(timezone=True))   # when operator applied it
    post_congestion_level = Column(Float)          # measured congestion after applying
    effectiveness_score = Column(Float)            # post vs pre improvement
