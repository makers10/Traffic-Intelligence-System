"""
API Key authentication middleware with role-based access control.

Two key tiers:
  - API_KEY        → "sensor" role  (ingest data, read predictions)
  - OPERATOR_API_KEY → "operator" role (resolve alerts, trigger training)

Auth bypass is allowed ONLY when both API_KEY is unset AND DEBUG is True.
"""
import logging
from enum import Enum
from typing import Optional

from fastapi import Request, HTTPException, WebSocket, WebSocketException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings

logger = logging.getLogger(__name__)

# Paths that never require an API key
PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class Role(str, Enum):
    SENSOR = "sensor"
    OPERATOR = "operator"


def _resolve_role(api_key: Optional[str]) -> Optional[Role]:
    """Map an API key string to a Role, or None if invalid."""
    if not api_key:
        return None
    if settings.get_operator_key() and api_key == settings.get_operator_key():
        return Role.OPERATOR
    if api_key == settings.API_KEY:
        return Role.SENSOR
    return None


def _is_auth_disabled() -> bool:
    """Auth bypass is allowed ONLY when no key is configured AND we
    are explicitly in debug mode."""
    return not settings.API_KEY and settings.DEBUG


# ── HTTP middleware ──────────────────────────────────────────────────────────

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Always allow public paths
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # WebSocket upgrades are handled in the WS endpoint itself
        if request.url.path.startswith("/ws"):
            return await call_next(request)

        # Dev-mode bypass: only when explicitly DEBUG=True AND no key set
        if _is_auth_disabled():
            request.state.role = Role.OPERATOR  # full access in dev
            return await call_next(request)

        # Extract key from header or query param
        api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
        role = _resolve_role(api_key)

        if role is None:
            raise HTTPException(status_code=401, detail="Invalid or missing API key")

        # Attach role to request state so route handlers can check it
        request.state.role = role
        return await call_next(request)


# ── WebSocket authentication ────────────────────────────────────────────────

def authenticate_ws(websocket: WebSocket) -> Role:
    """Validate the API key provided via query param on WebSocket handshake.

    Usage in WS endpoint::

        role = authenticate_ws(websocket)
    """
    if _is_auth_disabled():
        return Role.OPERATOR

    api_key = websocket.query_params.get("api_key")
    role = _resolve_role(api_key)

    if role is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    return role


# ── Route-level helpers ─────────────────────────────────────────────────────

def require_role(request: Request, minimum: Role = Role.SENSOR) -> Role:
    """FastAPI dependency to enforce a minimum role on a route.

    Usage::

        @router.patch("/alerts/{id}/resolve")
        def resolve(request: Request, role: Role = Depends(lambda r: require_role(r, Role.OPERATOR))):
            ...
    """
    role: Optional[Role] = getattr(request.state, "role", None)

    if role is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Operator > Sensor
    role_rank = {Role.SENSOR: 0, Role.OPERATOR: 1}
    if role_rank.get(role, -1) < role_rank.get(minimum, 99):
        raise HTTPException(
            status_code=403,
            detail=f"This action requires '{minimum.value}' role; you have '{role.value}'",
        )
    return role
