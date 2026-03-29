"""
WebSocket endpoint — pushes live traffic updates to connected clients.
Clients subscribe to a junction_id and receive updates every 10 seconds.
"""
import asyncio
import json
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.services.fusion_service import fused_prediction
from app.services.traffic_service import get_active_alerts

router = APIRouter()

# junction_id → set of connected websockets
_connections: dict[str, set[WebSocket]] = {}


async def _broadcast(junction_id: str, payload: dict):
    dead = set()
    for ws in _connections.get(junction_id, set()):
        try:
            await ws.send_text(json.dumps(payload, default=str))
        except Exception:
            dead.add(ws)
    _connections[junction_id] -= dead


@router.websocket("/ws/{junction_id}")
async def traffic_ws(junction_id: str, websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    _connections.setdefault(junction_id, set()).add(websocket)
    try:
        while True:
            # Push update every 10 seconds
            try:
                prediction = fused_prediction(db, junction_id)
                alerts = get_active_alerts(db, junction_id)
                payload = {
                    "type": "update",
                    "junction_id": junction_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "prediction": prediction,
                    "active_alerts": len(alerts),
                    "alert_severity": alerts[0].severity if alerts else None,
                }
            except Exception as e:
                payload = {"type": "error", "junction_id": junction_id, "message": str(e)}

            await websocket.send_text(json.dumps(payload, default=str))
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        _connections[junction_id].discard(websocket)
