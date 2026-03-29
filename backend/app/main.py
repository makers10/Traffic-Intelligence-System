from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.middleware.rate_limit import limiter
from app.middleware.auth import APIKeyMiddleware
from app.middleware.metrics import MetricsMiddleware, metrics_endpoint
from app.logging_config import setup_logging
from app.db import engine, Base
from app.models import traffic, weather, event, signal, transport  # noqa

from app.api.routes import router
from app.api.weather_routes import router as weather_router
from app.api.event_routes import router as event_router
from app.api.signal_routes import router as signal_router
from app.api.signal_feedback_routes import router as signal_feedback_router
from app.api.transport_routes import router as transport_router
from app.api.analytics_routes import router as analytics_router
from app.api.ml_routes import router as ml_router
from app.api.ws_routes import router as ws_router

setup_logging(debug=settings.DEBUG)

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Traffic Intelligence API",
    description="Real-time traffic prediction, accident detection, and analytics",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(MetricsMiddleware)
app.add_middleware(APIKeyMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(weather_router)
app.include_router(event_router)
app.include_router(signal_router)
app.include_router(signal_feedback_router)
app.include_router(transport_router)
app.include_router(analytics_router)
app.include_router(ml_router)
app.include_router(ws_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics", include_in_schema=False)
def metrics():
    return metrics_endpoint()
