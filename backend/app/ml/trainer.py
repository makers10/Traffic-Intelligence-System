"""
Model training pipeline.
Pulls historical readings from DB and trains per-junction models.
"""
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.traffic import TrafficReading
from app.ml.predictor import TrafficPredictor, build_feature_vector


def _congestion_from_reading(r: TrafficReading) -> float:
    """Derive a congestion label from raw sensor data (used as training target)."""
    speed_score = max(0.0, 1.0 - (r.speed_kmh / 80.0))
    density_score = min(r.vehicle_density / 200.0, 1.0)
    occupancy = (r.occupancy_pct or 0) / 100.0
    return round(min((speed_score * 0.5) + (density_score * 0.35) + (occupancy * 0.15), 1.0), 3)


def train_junction_model(db: Session, junction_id: str, days: int = 30) -> dict:
    """Train a GBM model for a single junction using last N days of readings."""
    since = datetime.utcnow() - timedelta(days=days)
    readings = db.query(TrafficReading).filter(
        TrafficReading.junction_id == junction_id,
        TrafficReading.timestamp >= since,
    ).order_by(TrafficReading.timestamp).all()

    if len(readings) < 50:
        return {"status": "skipped", "reason": f"Only {len(readings)} readings — need at least 50", "junction_id": junction_id}

    records = [
        {
            "speed_kmh": r.speed_kmh,
            "vehicle_density": r.vehicle_density,
            "occupancy_pct": r.occupancy_pct,
            "weather_condition": r.weather_condition,
            "visibility_m": r.visibility_m,
            "timestamp": r.timestamp,
            "congestion_level": _congestion_from_reading(r),
        }
        for r in readings
    ]

    predictor = TrafficPredictor(junction_id)
    predictor.train(records)

    return {
        "status": "trained",
        "junction_id": junction_id,
        "samples": len(records),
        "trained_at": datetime.utcnow().isoformat(),
    }


def train_all_junctions(db: Session, days: int = 30) -> list:
    """Train models for every junction that has data."""
    junction_ids = [
        row[0] for row in db.query(TrafficReading.junction_id).distinct().all()
    ]
    return [train_junction_model(db, jid, days) for jid in junction_ids]
