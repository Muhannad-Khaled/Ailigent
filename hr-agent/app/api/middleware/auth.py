"""API Key Authentication Middleware."""

import logging
import secrets
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

logger = logging.getLogger(__name__)

# Paths that don't require authentication
PUBLIC_PATHS = {
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/health",
    "/api/v1/health/",
}


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware to validate API key for protected routes."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Process request and validate API key."""
        path = request.url.path

        # Allow public paths
        if path in PUBLIC_PATHS or path.startswith("/api/v1/health"):
            return await call_next(request)

        # Check API key
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            logger.warning(f"Missing API key for request to {path}")
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "API key is missing",
                    "error": "unauthorized",
                },
            )

        if not settings.API_KEY:
            logger.error("API_KEY not configured in settings")
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Server configuration error",
                    "error": "internal_error",
                },
            )

        if not secrets.compare_digest(api_key, settings.API_KEY):
            logger.warning(f"Invalid API key attempt for {path}")
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "Invalid API key",
                    "error": "forbidden",
                },
            )

        return await call_next(request)
