from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas.signal import SignalOptimizeRequest, SignalPlanOut
from app.services import signal_service

router = APIRouter(prefix="/api/v1/signals", tags=["signals"])


@router.post("/optimize", response_model=SignalPlanOut)
def optimize_signal(payload: SignalOptimizeRequest, db: Session = Depends(get_db)):
    """Generate optimized signal timing for a junction based on current congestion."""
    result = signal_service.optimize_signal(db, payload.junction_id, payload.congestion_level)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
