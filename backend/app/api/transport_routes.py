from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.db import get_db
from app.schemas.transport import TransportReadingCreate, TransportReadingOut, TransportInsightOut
from app.services import transport_service

router = APIRouter(prefix="/api/v1/transport", tags=["transport"])


@router.post("", response_model=TransportReadingOut, status_code=201)
def ingest_transport(payload: TransportReadingCreate, db: Session = Depends(get_db)):
    """Ingest rideshare and transit volume data for a junction."""
    reading = transport_service.ingest_transport(db, payload)
    indices = {
        "road_pressure_index": reading.road_pressure_index,
        "transit_shift_score": reading.transit_shift_score,
    }
    insight = transport_service._insight(
        indices["road_pressure_index"],
        indices["transit_shift_score"],
        payload.rideshare_avg_wait_min,
    )
    return {**reading.__dict__, "insight": insight}


@router.get("/{junction_id}/insight", response_model=TransportInsightOut)
def transport_insight(
    junction_id: str,
    period_hours: int = Query(6, ge=1, le=48),
    db: Session = Depends(get_db),
):
    """Get multi-transport insight and modal shift analysis for a junction."""
    return transport_service.get_transport_insight(db, junction_id, period_hours)
