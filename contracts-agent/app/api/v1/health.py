"""Health check endpoints."""

from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.services.odoo.client import OdooClient, get_odoo_client
from app.services.ai.gemini_client import GeminiClient, get_gemini_client

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
@router.get("/")
async def health_check() -> Dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "contracts-agent"}


@router.get("/detailed")
async def detailed_health_check(
    odoo: OdooClient = Depends(get_odoo_client),
    gemini: GeminiClient = Depends(get_gemini_client),
) -> Dict[str, Any]:
    """
    Detailed health check with dependency status.

    Returns status of:
    - Odoo connection
    - Gemini AI service
    """
    odoo_status = odoo.check_connection()
    gemini_status = await gemini.health_check()

    overall_status = "healthy"
    if not odoo_status.get("connected"):
        overall_status = "degraded"
    if not gemini_status.get("available"):
        overall_status = "degraded" if overall_status == "healthy" else overall_status

    return {
        "status": overall_status,
        "service": "contracts-agent",
        "dependencies": {
            "odoo": odoo_status,
            "gemini": gemini_status,
        },
    }
