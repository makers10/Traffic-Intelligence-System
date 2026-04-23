from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.services import analytics_service, fusion_service

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/bulk-congestion")
def bulk_congestion(db: Session = Depends(get_db)):
    """Return the latest congestion level for every known junction in one response."""
    return analytics_service.bulk_congestion(db)


@router.get("/{junction_id}/summary")
def junction_summary(
    junction_id: str,
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
):
    """24h (or custom) summary stats for a junction."""
    result = analytics_service.junction_summary(db, junction_id, hours)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/{junction_id}/peak-hours")
def peak_hours(
    junction_id: str,
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
):
    """Hourly congestion breakdown over the last N days — useful for identifying peak patterns."""
    return analytics_service.peak_hours(db, junction_id, days)


@router.get("/{junction_id}/trend")
def congestion_trend(
    junction_id: str,
    hours: int = Query(6, ge=1, le=48),
    db: Session = Depends(get_db),
):
    """Recent congestion prediction trend for charting."""
    return analytics_service.congestion_trend(db, junction_id, hours)


@router.post("/{junction_id}/fused-predict")
def fused_predict(
    junction_id: str,
    horizon_minutes: int = Query(30, ge=5, le=120),
    db: Session = Depends(get_db),
):
    """
    Enhanced prediction fusing ML model + weather + event + transport data.
    Returns congestion forecast with contributing factors explained.
    """
    result = fusion_service.fused_prediction(db, junction_id, horizon_minutes)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
