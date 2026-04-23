from fastapi import APIRouter, Depends, BackgroundTasks, Request
from sqlalchemy.orm import Session
from app.db import get_db, db_session
from app.ml.trainer import train_junction_model, train_all_junctions
from app.middleware.auth import Role, require_role

router = APIRouter(prefix="/api/v1/ml", tags=["ml"])


@router.post("/train/{junction_id}")
def train_model(junction_id: str, request: Request, days: int = 30, db: Session = Depends(get_db)):
    """Trigger model training for a specific junction. Requires operator role."""
    require_role(request, Role.OPERATOR)
    return train_junction_model(db, junction_id, days)


def _train_all_background(days: int):
    """Run training in a background task with its own DB session.

    BackgroundTasks run AFTER the HTTP response is sent, so the
    request-scoped session from get_db() is already closed by then.
    We must create a fresh, independent session here.
    """
    with db_session() as db:
        train_all_junctions(db, days)


@router.post("/train-all")
def train_all(request: Request, days: int = 30, background_tasks: BackgroundTasks = BackgroundTasks()):
    """Trigger training for all junctions in the background. Requires operator role."""
    require_role(request, Role.OPERATOR)
    background_tasks.add_task(_train_all_background, days)
    return {"status": "training started", "days": days}
