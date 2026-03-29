from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.models.transport import TransportReading
from app.schemas.transport import TransportReadingCreate


def _compute_indices(rideshare: int, metro: int, bus: int) -> dict:
    """
    road_pressure_index: how much road-based transport dominates
    transit_shift_score: how much people are using public transit
    """
    total = rideshare + metro + bus
    if total == 0:
        return {"road_pressure_index": 0.5, "transit_shift_score": 0.5}

    road_pressure = rideshare / total
    transit_shift = (metro + bus) / total
    return {
        "road_pressure_index": round(road_pressure, 3),
        "transit_shift_score": round(transit_shift, 3),
    }


def _insight(road_pressure: float, transit_shift: float, wait_min: Optional[float]) -> str:
    if road_pressure > 0.75:
        return "High rideshare demand is adding road pressure. Consider promoting metro/bus alternatives."
    elif transit_shift > 0.65:
        return "Strong transit adoption. Road congestion likely lower than vehicle density suggests."
    elif wait_min and wait_min > 10:
        return "Long rideshare wait times indicate surge demand. Expect increased private vehicle usage."
    return "Balanced transport mix. No significant modal shift detected."


def ingest_transport(db: Session, data: TransportReadingCreate) -> TransportReading:
    indices = _compute_indices(data.rideshare_trips, data.metro_boardings, data.bus_boardings)
    reading = TransportReading(**data.model_dump(), **indices)
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


def get_transport_insight(db: Session, junction_id: str, period_hours: int = 6) -> dict:
    since = datetime.utcnow() - timedelta(hours=period_hours)
    result = db.query(
        func.avg(TransportReading.rideshare_trips).label("avg_rideshare"),
        func.avg(TransportReading.metro_boardings).label("avg_metro"),
        func.avg(TransportReading.bus_boardings).label("avg_bus"),
        func.avg(TransportReading.road_pressure_index).label("avg_road_pressure"),
        func.avg(TransportReading.transit_shift_score).label("avg_transit_shift"),
    ).filter(
        TransportReading.junction_id == junction_id,
        TransportReading.timestamp >= since,
    ).first()

    if not result or result.avg_rideshare is None:
        return {"error": "No transport data available for this junction"}

    road_p = float(result.avg_road_pressure or 0.5)
    transit_s = float(result.avg_transit_shift or 0.5)

    return {
        "junction_id": junction_id,
        "period_hours": period_hours,
        "avg_rideshare_trips": round(float(result.avg_rideshare), 1),
        "avg_metro_boardings": round(float(result.avg_metro), 1),
        "avg_bus_boardings": round(float(result.avg_bus), 1),
        "avg_road_pressure": round(road_p, 3),
        "avg_transit_shift": round(transit_s, 3),
        "recommendation": _insight(road_p, transit_s, None),
    }


def get_recent_transport(db: Session, junction_id: str, limit: int = 20) -> List[TransportReading]:
    return db.query(TransportReading).filter(
        TransportReading.junction_id == junction_id
    ).order_by(TransportReading.timestamp.desc()).limit(limit).all()
