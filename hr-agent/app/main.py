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
    logger.info("Starting HR Agent...")

    # Initialize Odoo connection
    try:
        odoo = get_odoo_client()
        odoo.connect()
        app.state.odoo = odoo
        logger.info("Odoo connection established")

        # Log available modules
        modules = odoo.get_available_modules_status()
        for module, available in modules.items():
            status = "available" if available else "NOT available"
            logger.info(f"  - {module}: {status}")

    except Exception as e:
        logger.warning(f"Odoo connection failed: {e}. API calls will retry on demand.")

    # Initialize scheduler
    try:
        from app.scheduler.scheduler import get_scheduler
        scheduler = get_scheduler()
        scheduler.start()
        app.state.scheduler = scheduler
        logger.info("Scheduler started with jobs registered")
    except Exception as e:
        logger.warning(f"Scheduler failed to start: {e}. Scheduled jobs will be unavailable.")

    logger.info("HR Agent started successfully")

    yield

    # Shutdown
    logger.info("Shutting down HR Agent...")

    # Shutdown scheduler
    if hasattr(app.state, "scheduler"):
        app.state.scheduler.shutdown()

    logger.info("HR Agent stopped")


# Create FastAPI application
app = FastAPI(
    title="HR Agent",
    description="""
    AI-powered HR automation system integrated with Odoo.

    ## Features
    - **Recruitment**: CV sorting, candidate ranking, interview scheduling
    - **Appraisals**: Performance review tracking, AI feedback summarization
    - **HR Reports**: Headcount, turnover, department metrics with AI insights
    - **Attendance Admin**: Leave approvals, anomaly detection, reporting

    ## Authentication
    All endpoints (except /health) require an API key via `X-API-Key` header.

    **API Key:** `ailigent-hr-api-key-2024`

    ## Integration
    This service integrates with:
    - Odoo ERP (HR modules)
    - Task Management Agent (for workflow automation)
    - Google Gemini AI (for intelligent analysis)
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[{"name": "HR Agent API"}],
    swagger_ui_parameters={"persistAuthorization": True},
)

# Add middleware (order matters - last added runs first)
app.add_middleware(LoggingMiddleware)
app.add_middleware(APIKeyMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


# Custom OpenAPI schema with API key authentication
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    # Add API Key security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "APIKeyHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "Enter your API key: ailigent-hr-api-key-2024"
        }
    }
    # Apply security to all endpoints
    openapi_schema["security"] = [{"APIKeyHeader": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "HR Agent",
        "version": "1.0.0",
        "description": "AI-powered HR automation system",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
