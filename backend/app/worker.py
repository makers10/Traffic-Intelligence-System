"""
Celery worker — background tasks for periodic model training and predictions.
Run with: celery -A app.worker worker --loglevel=info --beat
"""
from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery("traffic_intelligence", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

celery_app.conf.beat_schedule = {
    # Retrain all models every night at 2am
    "retrain-models-nightly": {
        "task": "app.worker.retrain_all_models",
        "schedule": crontab(hour=2, minute=0),
    },
    # Run fused predictions for all junctions every 5 minutes
    "refresh-predictions": {
        "task": "app.worker.refresh_all_predictions",
        "schedule": 300.0,  # seconds
    },
}
celery_app.conf.timezone = "UTC"


@celery_app.task(name="app.worker.retrain_all_models")
def retrain_all_models():
    from app.db import db_session
    from app.ml.trainer import train_all_junctions
    with db_session() as db:
        return train_all_junctions(db)


@celery_app.task(name="app.worker.retrain_junction_model")
def retrain_junction_model(junction_id: str, days: int = 30):
    from app.db import db_session
    from app.ml.trainer import train_junction_model
    with db_session() as db:
        return train_junction_model(db, junction_id, days)


@celery_app.task(name="app.worker.refresh_all_predictions")
def refresh_all_predictions():
    from app.db import db_session
    from app.models.traffic import TrafficReading
    from app.services.fusion_service import fused_prediction

    with db_session() as db:
        junction_ids = [
            row[0] for row in db.query(TrafficReading.junction_id).distinct().all()
        ]

    # Process each junction with its own session so a failure in one
    # junction doesn't roll back or poison the session for the rest.
    results = []
    for jid in junction_ids:
        try:
            with db_session() as db:
                result = fused_prediction(db, jid)
                results.append({"junction_id": jid, "status": "ok", "level": result.get("congestion_level")})
        except Exception as e:
            results.append({"junction_id": jid, "status": "error", "error": str(e)})
    return results
