from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.db import get_db
from app.ml.trainer import train_junction_model, train_all_junctions

router = APIRouter(prefix="/api/v1/ml", tags=["ml"])


@router.post("/train/{junction_id}")
def train_model(junction_id: str, days: int = 30, db: Session = Depends(get_db)):
    """Trigger model training for a specific junction."""
    return train_junction_model(db, junction_id, days)


@router.post("/train-all")
def train_all(days: int = 30, background_tasks: BackgroundTasks = BackgroundTasks(), db: Session = Depends(get_db)):
    """Trigger training for all junctions in the background."""
    background_tasks.add_task(train_all_junctions, db, days)
    return {"status": "training started", "days": days}
