import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger
from telegram.ext import Application

from app.config import get_settings
from app.handlers import setup_handlers
from app.services import OdooService, GeminiService
from app.mcp import create_odoo_mcp_server

settings = get_settings()

# Global instances
telegram_app: Application = None
odoo_service: OdooService = None
gemini_service: GeminiService = None
mcp_server = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global telegram_app, odoo_service, gemini_service, mcp_server

    logger.info("Starting Ailigent Employee Agent...")

    # Initialize Odoo service
    odoo_service = OdooService(
        url=settings.odoo_url,
        db=settings.odoo_db,
        username=settings.odoo_username,
        password=settings.odoo_password,
    )
    await odoo_service.connect()
    logger.info("Connected to Odoo")

    # Create MCP server with Odoo integration
    mcp_server = create_odoo_mcp_server(odoo_service)
    logger.info("Initialized Odoo MCP Server")

    # Initialize Gemini AI with Odoo service for MCP tools
    gemini_service = GeminiService(
        api_key=settings.google_api_key,
        odoo_service=odoo_service,  # Enable MCP-style function calling
    )
    logger.info("Initialized Gemini AI with MCP tools")

    # Initialize Telegram bot
    telegram_app = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .build()
    )

    # Setup handlers with services
    setup_handlers(telegram_app, odoo_service, gemini_service)

    # Start polling in background
    await telegram_app.initialize()
    await telegram_app.start()
    asyncio.create_task(telegram_app.updater.start_polling(drop_pending_updates=True))
    logger.info("Telegram bot started")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()


app = FastAPI(
    title="Ailigent - Internal Employee Agent",
    description="AI-powered Telegram bot for employee inquiries with Odoo integration",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {
        "name": "Ailigent Employee Agent",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "odoo_connected": odoo_service.is_connected if odoo_service else False,
        "telegram_running": telegram_app.running if telegram_app else False,
        "mcp_enabled": mcp_server is not None,
    }


@app.get("/mcp/tools")
async def list_mcp_tools():
    """List available MCP tools"""
    return {
        "server": "Odoo Employee Agent",
        "tools": [
            {"name": "get_employee_info", "description": "Get employee details"},
            {"name": "get_leave_balance", "description": "Get leave balance"},
            {"name": "get_leave_requests", "description": "Get leave requests"},
            {"name": "get_payslips", "description": "Get payslips"},
            {"name": "get_attendance_summary", "description": "Get attendance"},
            {"name": "get_employee_tasks", "description": "Get tasks"},
            {"name": "create_task", "description": "Create a task"},
            {"name": "get_company_policies", "description": "Get policies"},
            {"name": "check_telegram_link", "description": "Check account link"},
            {"name": "link_telegram_account", "description": "Link account"},
            {"name": "unlink_telegram_account", "description": "Unlink account"},
        ],
        "resources": [
            {"uri": "employee://{employee_id}/summary", "description": "Employee summary"},
            {"uri": "policies://list", "description": "Policy list"},
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
