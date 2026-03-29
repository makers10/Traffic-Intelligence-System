from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.models.traffic import TrafficReading, CongestionPrediction, AccidentAlert


def junction_summary(db: Session, junction_id: str, hours: int = 24) -> dict:
    since = datetime.utcnow() - timedelta(hours=hours)

    stats = db.query(
        func.avg(TrafficReading.speed_kmh).label("avg_speed"),
        func.min(TrafficReading.speed_kmh).label("min_speed"),
        func.max(TrafficReading.speed_kmh).label("max_speed"),
        func.avg(TrafficReading.vehicle_density).label("avg_density"),
        func.count(TrafficReading.id).label("total_readings"),
    ).filter(
        TrafficReading.junction_id == junction_id,
        TrafficReading.timestamp >= since,
    ).first()

    alert_count = db.query(func.count(AccidentAlert.id)).filter(
        AccidentAlert.junction_id == junction_id,
        AccidentAlert.detected_at >= since,
    ).scalar()

    if not stats or not stats.total_readings:
        return {"error": "No data for this junction in the given period"}

    return {
        "junction_id": junction_id,
        "period_hours": hours,
        "avg_speed_kmh": round(float(stats.avg_speed), 1),
        "min_speed_kmh": round(float(stats.min_speed), 1),
        "max_speed_kmh": round(float(stats.max_speed), 1),
        "avg_vehicle_density": round(float(stats.avg_density), 1),
        "total_readings": stats.total_readings,
        "accident_alerts": alert_count,
    }


def peak_hours(db: Session, junction_id: str, days: int = 7) -> list:
    """Returns avg congestion by hour-of-day over the last N days."""
    since = datetime.utcnow() - timedelta(days=days)

    rows = db.query(
        extract("hour", TrafficReading.timestamp).label("hour"),
        func.avg(TrafficReading.vehicle_density).label("avg_density"),
        func.avg(TrafficReading.speed_kmh).label("avg_speed"),
        func.count(TrafficReading.id).label("samples"),
    ).filter(
        TrafficReading.junction_id == junction_id,
        TrafficReading.timestamp >= since,
    ).group_by("hour").order_by("hour").all()

    result = []
    for row in rows:
        speed_score = max(0.0, 1.0 - (float(row.avg_speed) / 80.0))
        density_score = min(float(row.avg_density) / 200.0, 1.0)
        congestion = round((speed_score * 0.5) + (density_score * 0.5), 3)
        result.append({
            "hour": int(row.hour),
            "avg_speed_kmh": round(float(row.avg_speed), 1),
            "avg_density": round(float(row.avg_density), 1),
            "congestion_estimate": congestion,
            "samples": int(row.samples),
        })
    return result


def congestion_trend(db: Session, junction_id: str, hours: int = 6) -> list:
    """Returns stored predictions over the last N hours for trend visualization."""
    since = datetime.utcnow() - timedelta(hours=hours)
    rows = db.query(CongestionPrediction).filter(
        CongestionPrediction.junction_id == junction_id,
        CongestionPrediction.predicted_at >= since,
    ).order_by(CongestionPrediction.predicted_at).all()

    return [
        {
            "predicted_at": r.predicted_at,
            "forecast_time": r.forecast_time,
            "congestion_level": r.congestion_level,
            "predicted_speed": r.predicted_speed,
            "confidence": r.confidence,
        }
        for r in rows
    ]
