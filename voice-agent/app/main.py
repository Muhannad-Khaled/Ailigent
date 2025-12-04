"""Voice Agent - FastAPI + LiveKit Agent Entry Point."""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.services.odoo_service import get_odoo_service
from app.agent.voice_agent import run_agent

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    logger.info("Starting Voice Agent...")

    # Initialize Odoo connection
    try:
        odoo = get_odoo_service()
        if odoo.is_connected:
            logger.info("Odoo connection established")
        else:
            logger.warning("Odoo not connected - will retry on demand")
    except Exception as e:
        logger.warning(f"Odoo connection failed: {e}")

    logger.info("Voice Agent started successfully")
    logger.info(f"LiveKit URL: {settings.LIVEKIT_URL}")

    yield

    # Shutdown
    logger.info("Shutting down Voice Agent...")
    logger.info("Voice Agent stopped")


# Create FastAPI application
app = FastAPI(
    title="Voice Agent",
    description="""
    LiveKit-powered Voice AI Agent for Ailigent Suite.

    ## Features
    - Voice interaction with Odoo ERP
    - Employee self-service (leave, payslips, attendance, tasks)
    - Task management integration
    - HR management for managers
    - Contract management
    - Bilingual support (English/Arabic)

    ## Running the Voice Agent
    The voice agent runs as a LiveKit worker. Start it with:
    ```bash
    python -m app.agent.voice_agent
    ```

    Or use the API to check status and health.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Voice Agent",
        "version": "1.0.0",
        "description": "LiveKit Voice AI for Ailigent Suite",
        "livekit_url": settings.LIVEKIT_URL,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    odoo = get_odoo_service()
    return {
        "status": "healthy",
        "odoo_connected": odoo.is_connected,
        "livekit_configured": bool(settings.LIVEKIT_API_KEY),
        "google_ai_configured": bool(settings.GOOGLE_API_KEY),
    }


@app.get("/config")
async def get_config():
    """Get non-sensitive configuration."""
    return {
        "livekit_url": settings.LIVEKIT_URL,
        "default_language": settings.DEFAULT_LANGUAGE,
        "voice_en": settings.VOICE_EN,
        "voice_ar": settings.VOICE_AR,
        "services": {
            "employee_agent": settings.EMPLOYEE_AGENT_URL,
            "task_management": settings.TASK_MANAGEMENT_URL,
            "hr_agent": settings.HR_AGENT_URL,
            "contracts_agent": settings.CONTRACTS_AGENT_URL,
        }
    }


if __name__ == "__main__":
    import uvicorn

    # Check if we should run as LiveKit agent or FastAPI
    import sys
    if "--agent" in sys.argv:
        # Run as LiveKit agent worker
        logger.info("Starting LiveKit agent worker...")
        run_agent()
    else:
        # Run FastAPI server
        uvicorn.run(
            "app.main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
        )
