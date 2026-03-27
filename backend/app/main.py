from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.api.weather_routes import router as weather_router
from app.api.event_routes import router as event_router
from app.api.signal_routes import router as signal_router
from app.db import engine, Base
from app.models import traffic, weather, event, signal

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Traffic Intelligence API",
    description="Phase 1: Traffic prediction and accident detection",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(weather_router)
app.include_router(event_router)
app.include_router(signal_router)


@app.get("/health")
def health():
    return {"status": "ok"}
