"""Health Check Endpoints."""

from typing import Any, Dict

from fastapi import APIRouter

from app.services.odoo.client import get_odoo_client
from app.services.ai.gemini_client import get_gemini_client

router = APIRouter()


@router.get("")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "hr-agent",
        "version": "1.0.0",
    }


@router.get("/odoo")
async def health_odoo() -> Dict[str, Any]:
    """Check Odoo connection status."""
    client = get_odoo_client()
    status = client.check_connection()
    return {
        "service": "odoo",
        **status,
    }


@router.get("/gemini")
async def health_gemini() -> Dict[str, Any]:
    """Check Gemini AI status."""
    client = get_gemini_client()
    status = await client.health_check()
    return {
        "service": "gemini",
        **status,
    }


@router.get("/modules")
async def health_modules() -> Dict[str, Any]:
    """Check available Odoo HR modules."""
    client = get_odoo_client()
    try:
        client.ensure_connected()
        modules = client.get_available_modules_status()
        return {
            "status": "checked",
            "modules": modules,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@router.get("/all")
async def health_all() -> Dict[str, Any]:
    """Comprehensive health check of all services."""
    odoo_client = get_odoo_client()
    gemini_client = get_gemini_client()

    odoo_status = odoo_client.check_connection()
    gemini_status = await gemini_client.health_check()

    # Determine overall health
    all_healthy = odoo_status.get("connected", False) and gemini_status.get("available", False)

    return {
        "status": "healthy" if all_healthy else "degraded",
        "service": "hr-agent",
        "version": "1.0.0",
        "components": {
            "odoo": {
                "healthy": odoo_status.get("connected", False),
                **odoo_status,
            },
            "gemini": {
                "healthy": gemini_status.get("available", False),
                **gemini_status,
            },
        },
    }
