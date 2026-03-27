from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.db import engine, Base

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


@app.get("/health")
def health():
    return {"status": "ok"}
