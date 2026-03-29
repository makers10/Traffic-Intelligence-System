from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from app.db import get_db
from app.models.signal import SignalPlan

router = APIRouter(prefix="/api/v1/signals", tags=["signals"])


class FeedbackPayload(BaseModel):
    post_congestion_level: float = Field(..., ge=0.0, le=1.0)
    notes: Optional[str] = None


@router.post("/{plan_id}/apply")
def mark_applied(plan_id: int, db: Session = Depends(get_db)):
    """Mark a signal plan as applied by the operator."""
    plan = db.query(SignalPlan).filter(SignalPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Signal plan not found")
    plan.applied_at = datetime.utcnow()
    db.commit()
    return {"status": "applied", "plan_id": plan_id, "applied_at": plan.applied_at}


@router.post("/{plan_id}/feedback")
def submit_feedback(plan_id: int, payload: FeedbackPayload, db: Session = Depends(get_db)):
    """Submit post-application congestion reading to measure effectiveness."""
    plan = db.query(SignalPlan).filter(SignalPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Signal plan not found")
    if plan.congestion_level is None:
        raise HTTPException(status_code=400, detail="Plan has no baseline congestion level")

    improvement = plan.congestion_level - payload.post_congestion_level
    plan.post_congestion_level = payload.post_congestion_level
    plan.effectiveness_score = round(max(improvement, 0.0), 3)
    db.commit()

    return {
        "plan_id": plan_id,
        "pre_congestion": plan.congestion_level,
        "post_congestion": payload.post_congestion_level,
        "improvement": round(improvement * 100, 1),
        "effectiveness_score": plan.effectiveness_score,
        "verdict": "effective" if improvement > 0.05 else "marginal" if improvement > 0 else "no improvement",
    }
