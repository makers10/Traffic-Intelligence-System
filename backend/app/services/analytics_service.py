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


def bulk_congestion(db: Session) -> dict:
    """
    Return the latest congestion level for every junction in a single query.
    Falls back to a heuristic from the most recent TrafficReading when no
    stored prediction exists.
    """
    from sqlalchemy import desc

    # ── 1. Latest stored prediction per junction (single query) ──────────
    latest_sub = (
        db.query(
            CongestionPrediction.junction_id,
            func.max(CongestionPrediction.predicted_at).label("max_ts"),
        )
        .group_by(CongestionPrediction.junction_id)
        .subquery()
    )
    predictions = (
        db.query(
            CongestionPrediction.junction_id,
            CongestionPrediction.congestion_level,
            CongestionPrediction.predicted_speed,
            CongestionPrediction.confidence,
        )
        .join(
            latest_sub,
            (CongestionPrediction.junction_id == latest_sub.c.junction_id)
            & (CongestionPrediction.predicted_at == latest_sub.c.max_ts),
        )
        .all()
    )

    result: dict[str, dict] = {}
    for row in predictions:
        result[row.junction_id] = {
            "junction_id": row.junction_id,
            "congestion_level": round(float(row.congestion_level), 3),
            "predicted_speed": round(float(row.predicted_speed), 1) if row.predicted_speed else None,
            "confidence": round(float(row.confidence), 2) if row.confidence else None,
        }

    # ── 2. Fallback: junctions that have readings but no prediction yet ──
    reading_sub = (
        db.query(
            TrafficReading.junction_id,
            func.max(TrafficReading.timestamp).label("max_ts"),
        )
        .group_by(TrafficReading.junction_id)
        .subquery()
    )
    latest_readings = (
        db.query(
            TrafficReading.junction_id,
            TrafficReading.speed_kmh,
            TrafficReading.vehicle_density,
        )
        .join(
            reading_sub,
            (TrafficReading.junction_id == reading_sub.c.junction_id)
            & (TrafficReading.timestamp == reading_sub.c.max_ts),
        )
        .all()
    )

    for row in latest_readings:
        if row.junction_id in result:
            continue  # already have a prediction
        speed_score = max(0.0, 1.0 - (row.speed_kmh / 80.0))
        density_score = min(row.vehicle_density / 200.0, 1.0)
        level = round(min(max((speed_score * 0.5) + (density_score * 0.35), 0.0), 1.0), 3)
        result[row.junction_id] = {
            "junction_id": row.junction_id,
            "congestion_level": level,
            "predicted_speed": None,
            "confidence": 0.4,  # low confidence — heuristic fallback
        }

    return result
