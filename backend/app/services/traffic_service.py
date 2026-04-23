from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Optional

from app.models.traffic import TrafficReading, CongestionPrediction, AccidentAlert
from app.schemas.traffic import TrafficReadingCreate
from app.ml.predictor import TrafficPredictor
from app.ml import accident_detector


BASELINE_WINDOW_MINUTES = 30
BASELINE_MIN_READINGS = 3


def ingest_reading(db: Session, data: TrafficReadingCreate) -> TrafficReading:
    reading = TrafficReading(**data.model_dump())
    db.add(reading)
    db.commit()
    db.refresh(reading)

    # Run accident detection on every new reading
    _check_accident(db, reading)
    return reading


def _get_baseline(db: Session, junction_id: str) -> Optional[dict]:
    """Rolling average AND stddev of last 30 minutes for a junction.

    Returns mean and standard deviation so the accident detector can
    use z-score analysis instead of brittle percentage thresholds.
    """
    since = datetime.utcnow() - timedelta(minutes=BASELINE_WINDOW_MINUTES)
    result = db.query(
        func.avg(TrafficReading.speed_kmh).label("avg_speed"),
        func.avg(TrafficReading.vehicle_density).label("avg_density"),
        func.count(TrafficReading.id).label("count"),
        func.stddev_pop(TrafficReading.speed_kmh).label("stddev_speed"),
        func.stddev_pop(TrafficReading.vehicle_density).label("stddev_density"),
    ).filter(
        TrafficReading.junction_id == junction_id,
        TrafficReading.timestamp >= since,
    ).first()

    if not result or result.count < BASELINE_MIN_READINGS:
        return None
    return {
        "speed": float(result.avg_speed),
        "density": float(result.avg_density),
        "stddev_speed": float(result.stddev_speed or 0),
        "stddev_density": float(result.stddev_density or 0),
    }


def _check_accident(db: Session, reading: TrafficReading):
    baseline = _get_baseline(db, reading.junction_id)
    if not baseline:
        return

    alert = accident_detector.detect(
        current_speed=reading.speed_kmh,
        baseline_speed=baseline["speed"],
        current_density=reading.vehicle_density,
        baseline_density=int(baseline["density"]),
        occupancy_pct=reading.occupancy_pct,
        speed_stddev=baseline["stddev_speed"],
        density_stddev=baseline["stddev_density"],
    )

    if alert:
        db.add(AccidentAlert(
            junction_id=reading.junction_id,
            severity=alert["severity"],
            speed_drop_pct=alert["speed_drop_pct"],
            density_spike_pct=alert["density_spike_pct"],
        ))
        db.commit()



def predict_congestion(db: Session, junction_id: str, horizon_minutes: int) -> dict:
    # Fetch latest reading for this junction
    latest = db.query(TrafficReading).filter(
        TrafficReading.junction_id == junction_id
    ).order_by(TrafficReading.timestamp.desc()).first()

    if not latest:
        return {"error": "No data available for this junction"}

    predictor = TrafficPredictor(junction_id)
    result = predictor.predict(
        speed_kmh=latest.speed_kmh,
        vehicle_density=latest.vehicle_density,
        occupancy_pct=latest.occupancy_pct,
        weather_condition=latest.weather_condition,
        visibility_m=latest.visibility_m,
        horizon_minutes=horizon_minutes,
    )

    # Persist prediction
    db.add(CongestionPrediction(
        junction_id=junction_id,
        forecast_time=result["forecast_time"],
        congestion_level=result["congestion_level"],
        predicted_speed=result["predicted_speed"],
        confidence=result["confidence"],
    ))
    db.commit()
    return result


def get_active_alerts(db: Session, junction_id: Optional[str] = None) -> List[AccidentAlert]:
    q = db.query(AccidentAlert).filter(AccidentAlert.resolved_at.is_(None))
    if junction_id:
        q = q.filter(AccidentAlert.junction_id == junction_id)
    return q.order_by(AccidentAlert.detected_at.desc()).limit(50).all()


def get_recent_readings(db: Session, junction_id: str, limit: int = 20) -> List[TrafficReading]:
    return db.query(TrafficReading).filter(
        TrafficReading.junction_id == junction_id
    ).order_by(TrafficReading.timestamp.desc()).limit(limit).all()
