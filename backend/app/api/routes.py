from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db
from app.schemas.traffic import (
    TrafficReadingCreate, TrafficReadingOut,
    PredictionRequest, PredictionOut,
    AccidentAlertOut,
)
from app.services import traffic_service
from app.middleware.auth import Role, require_role

router = APIRouter(prefix="/api/v1", tags=["traffic"])


@router.post("/readings", response_model=TrafficReadingOut, status_code=201)
def ingest_reading(payload: TrafficReadingCreate, db: Session = Depends(get_db)):
    """Ingest a new traffic sensor reading. Triggers accident detection automatically."""
    return traffic_service.ingest_reading(db, payload)


@router.get("/readings/{junction_id}", response_model=List[TrafficReadingOut])
def get_readings(
    junction_id: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return traffic_service.get_recent_readings(db, junction_id, limit)


@router.post("/predict", response_model=PredictionOut)
def predict(payload: PredictionRequest, db: Session = Depends(get_db)):
    """Predict congestion level for a junction N minutes ahead."""
    result = traffic_service.predict_congestion(db, payload.junction_id, payload.horizon_minutes)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/alerts", response_model=List[AccidentAlertOut])
def get_alerts(
    junction_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Get all unresolved accident alerts, optionally filtered by junction."""
    return traffic_service.get_active_alerts(db, junction_id)


@router.patch("/alerts/{alert_id}/resolve", response_model=AccidentAlertOut)
def resolve_alert(alert_id: int, request: Request, db: Session = Depends(get_db)):
    """Mark an accident alert as resolved.

    Requires the 'operator' role — sensors cannot resolve alerts.
    """
    require_role(request, Role.OPERATOR)

    from app.models.traffic import AccidentAlert
    from datetime import datetime
    alert = db.query(AccidentAlert).filter(AccidentAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)
    return alert
