from datetime import datetime
from sqlalchemy.orm import Session
from app.services.traffic_service import predict_congestion
from app.services.event_service import get_event_impact
from app.services.transport_service import get_transport_insight


def fused_prediction(db: Session, junction_id: str, horizon_minutes: int = 30) -> dict:
    """
    Combines base ML prediction with weather, event, and transport context
    to produce an enriched congestion forecast.
    """
    base = predict_congestion(db, junction_id, horizon_minutes)
    if "error" in base:
        return base

    event_impact = get_event_impact(db, junction_id)
    transport = get_transport_insight(db, junction_id, period_hours=2)

    road_pressure = transport.get("avg_road_pressure", 0.5) if "error" not in transport else 0.5

    # Weighted fusion: base model carries most weight
    raw_level = (
        base["congestion_level"] * 0.60 +
        event_impact * 0.25 +
        road_pressure * 0.15
    )
    fused_level = round(min(max(raw_level, 0.0), 1.0), 3)

    label_map = [
        (0.25, "free"), (0.50, "moderate"), (0.75, "heavy"), (1.01, "standstill")
    ]
    label = next(l for threshold, l in label_map if fused_level < threshold)

    factors = []
    if event_impact > 0.3:
        factors.append(f"nearby event (impact={event_impact:.0%})")
    if road_pressure > 0.6:
        factors.append("high rideshare demand adding road pressure")
    if base["congestion_level"] > 0.5:
        factors.append("elevated base congestion from sensor data")

    return {
        **base,
        "congestion_level": fused_level,
        "label": label,
        "event_impact": event_impact,
        "road_pressure_index": road_pressure,
        "contributing_factors": factors or ["No significant external factors"],
        "fusion": True,
    }
