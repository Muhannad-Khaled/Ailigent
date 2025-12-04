"""FastAPI Application Entry Point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.router import api_router
from app.api.middleware.auth import APIKeyMiddleware
from app.api.middleware.logging import LoggingMiddleware
from app.services.cache.redis_client import get_redis_client
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
    logger.info("Starting Task Management Agent...")

    # Initialize Redis connection
    try:
        redis = await get_redis_client()
        app.state.redis = redis
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Some features may be unavailable.")

    # Initialize Odoo connection
    try:
        odoo = get_odoo_client()
        odoo.connect()
        app.state.odoo = odoo
        logger.info("Odoo connection established")
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

    logger.info("Task Management Agent started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Task Management Agent...")

    # Shutdown scheduler
    if hasattr(app.state, "scheduler"):
        app.state.scheduler.shutdown()

    # Disconnect Redis
    if hasattr(app.state, "redis"):
        await app.state.redis.disconnect()

    logger.info("Task Management Agent stopped")


# Create FastAPI application
app = FastAPI(
    title="Task Management Agent",
    description="""
    AI-powered task distribution and tracking system integrated with Odoo.

    ## Features
    - **Task Management**: List, update, and assign tasks
    - **Workload Analysis**: Monitor employee workload and utilization
    - **Productivity Reports**: Generate insights on task completion
    - **Smart Distribution**: AI-powered task assignment recommendations
    - **Alerts**: Automatic notifications for overdue tasks

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
    allow_origins=settings.ALLOWED_ORIGINS,
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
        "name": "Task Management Agent",
        "version": "1.0.0",
        "description": "AI-powered task distribution and tracking system",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
