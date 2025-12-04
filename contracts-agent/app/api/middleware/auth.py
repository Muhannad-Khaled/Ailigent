"""API Key Authentication Middleware."""

import logging

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

logger = logging.getLogger(__name__)


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware to validate API key for protected endpoints."""

    # Paths that don't require authentication
    EXCLUDED_PATHS = {
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/health",
        "/api/v1/health/",
    }

    async def dispatch(self, request: Request, call_next) -> Response:
        """Check API key for protected endpoints."""
        path = request.url.path

        # Skip authentication for excluded paths
        if path in self.EXCLUDED_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        # Check API key
        api_key = request.headers.get("X-API-Key")

        if not settings.API_KEY:
            # No API key configured, allow all requests (development mode)
            logger.warning("API_KEY not configured. Running in open mode.")
            return await call_next(request)

        if not api_key:
            return Response(
                content='{"detail": "Missing API key. Include X-API-Key header."}',
                status_code=401,
                media_type="application/json",
            )

        if api_key != settings.API_KEY:
            logger.warning(f"Invalid API key attempt from {request.client.host}")
            return Response(
                content='{"detail": "Invalid API key"}',
                status_code=403,
                media_type="application/json",
            )

        return await call_next(request)
