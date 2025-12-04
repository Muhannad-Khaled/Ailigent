"""FastAPI Application Entry Point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.config import settings
from app.api.router import api_router
from app.api.middleware.auth import APIKeyMiddleware
from app.api.middleware.logging import LoggingMiddleware
from app.services.odoo.client import get_odoo_client

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    logger.info("Starting Contracts Agent...")

    # Initialize Odoo connection
    try:
        odoo = get_odoo_client()
        odoo.connect()
        app.state.odoo = odoo
        logger.info("Odoo connection established")
    except Exception as e:
        logger.warning(f"Odoo connection failed: {e}. API calls will retry on demand.")

    # Initialize scheduler (will be added later)
    try:
        from app.scheduler.scheduler import get_scheduler
        scheduler = get_scheduler()
        scheduler.start()
        app.state.scheduler = scheduler
        logger.info("Scheduler started with jobs registered")
    except Exception as e:
        logger.warning(f"Scheduler failed to start: {e}. Scheduled jobs will be unavailable.")

    logger.info("Contracts Agent started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Contracts Agent...")

    # Shutdown scheduler
    if hasattr(app.state, "scheduler"):
        app.state.scheduler.shutdown()

    logger.info("Contracts Agent stopped")


# Create FastAPI application
app = FastAPI(
    title="Contracts Agent",
    description="""
    AI-powered Contract Lifecycle Management system integrated with Odoo.

    ## Features
    - **Contract Management**: CRUD operations for contracts linked to Odoo documents
    - **AI Analysis**: Extract and analyze clauses using Gemini AI
    - **Milestone Tracking**: Monitor delivery dates and deadlines
    - **Compliance Monitoring**: Track compliance requirements and scores
    - **Expiry Alerts**: Scheduled notifications for expiring contracts
    - **Reports**: Portfolio, expiry, compliance, and risk reports

    ## Authentication
    All endpoints (except /health) require an API key via `X-API-Key` header.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add middleware (order matters - last added runs first)
app.add_middleware(LoggingMiddleware)
app.add_middleware(APIKeyMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Contracts Agent",
        "version": "1.0.0",
        "description": "AI-powered Contract Lifecycle Management system",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


def custom_openapi():
    """Custom OpenAPI schema with API key security."""
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Contracts Agent",
        version="1.0.0",
        description="""
        AI-powered Contract Lifecycle Management system integrated with Odoo.

        ## Authentication
        All endpoints (except /health) require an API key via `X-API-Key` header.
        """,
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
        }
    }
    openapi_schema["security"] = [{"ApiKeyAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
