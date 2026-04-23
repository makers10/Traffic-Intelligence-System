"""
WebSocket endpoint — pushes live traffic updates to connected clients.
Clients subscribe to a junction_id and receive updates every 10 seconds.

Authentication: clients must provide a valid api_key query parameter
on the handshake, e.g.  ws://host/ws/J001?api_key=<key>
"""
import asyncio
import json
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.db import db_session
from app.middleware.auth import authenticate_ws
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
async def traffic_ws(junction_id: str, websocket: WebSocket):
    """Push live traffic updates every 10 seconds.

    Authenticates on handshake — rejects unauthenticated clients with
    WS 1008 (Policy Violation) before accepting the connection.

    Each update cycle creates a short-lived DB session instead of
    holding a single session open for the lifetime of the connection.
    """
    # Authenticate BEFORE accepting — invalid key = immediate rejection
    role = authenticate_ws(websocket)

    await websocket.accept()
    _connections.setdefault(junction_id, set()).add(websocket)
    try:
        while True:
            try:
                # Fresh session per cycle — no stale state across the 10s gap
                with db_session() as db:
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
