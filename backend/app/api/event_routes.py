from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import get_db
from app.schemas.event import EventCreate, EventOut
from app.services import event_service

router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.post("", response_model=EventOut, status_code=201)
def create_event(payload: EventCreate, db: Session = Depends(get_db)):
    """Register a new event (concert, match, protest, etc.) and compute its traffic impact."""
    return event_service.create_event(db, payload)


@router.get("", response_model=List[EventOut])
def list_active_events(
    junction_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List all currently active or upcoming events within 2 hours."""
    return event_service.get_active_events(db, junction_id)


@router.get("/{junction_id}/impact")
def event_impact(junction_id: str, db: Session = Depends(get_db)):
    """Get combined event impact score for a junction."""
    score = event_service.get_event_impact(db, junction_id)
    return {"junction_id": junction_id, "event_impact_score": score}
