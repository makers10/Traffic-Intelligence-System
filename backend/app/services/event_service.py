from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.event import TrafficEvent
from app.schemas.event import EventCreate


# Attendance → impact score mapping
def _attendance_impact(attendance: Optional[int]) -> float:
    if not attendance:
        return 0.3
    if attendance < 1000:
        return 0.2
    elif attendance < 5000:
        return 0.4
    elif attendance < 20000:
        return 0.65
    return 0.9


EVENT_TYPE_MULTIPLIER = {
    "concert": 1.0, "match": 1.1, "festival": 0.9,
    "protest": 1.2, "conference": 0.7, "other": 0.8,
}


def create_event(db: Session, data: EventCreate) -> TrafficEvent:
    impact = _attendance_impact(data.expected_attendance)
    multiplier = EVENT_TYPE_MULTIPLIER.get(data.event_type.lower(), 0.8)
    event = TrafficEvent(
        **data.model_dump(),
        impact_score=round(min(impact * multiplier, 1.0), 3),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_active_events(db: Session, junction_id: Optional[str] = None) -> List[TrafficEvent]:
    now = datetime.utcnow()
    q = db.query(TrafficEvent).filter(
        TrafficEvent.starts_at <= now + timedelta(hours=2),
        TrafficEvent.is_active == True,
    ).filter(
        (TrafficEvent.ends_at == None) | (TrafficEvent.ends_at >= now)
    )
    if junction_id:
        q = q.filter(TrafficEvent.junction_id == junction_id)
    return q.order_by(TrafficEvent.starts_at).all()


def get_event_impact(db: Session, junction_id: str) -> float:
    """Returns combined impact score of all active events near a junction."""
    events = get_active_events(db, junction_id)
    if not events:
        return 0.0
    # Take the max impact (events don't simply add up)
    return max(e.impact_score for e in events if e.impact_score)
