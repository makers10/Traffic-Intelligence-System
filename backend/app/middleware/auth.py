from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings

# Paths that don't require an API key
PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth if no API key is configured (dev mode)
        if not settings.API_KEY:
            return await call_next(request)

        # Skip public paths and WebSocket upgrades
        if request.url.path in PUBLIC_PATHS or request.url.path.startswith("/ws"):
            return await call_next(request)

        api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
        if api_key != settings.API_KEY:
            raise HTTPException(status_code=401, detail="Invalid or missing API key")

        return await call_next(request)
