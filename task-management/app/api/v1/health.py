"""Health check endpoints."""

from fastapi import APIRouter

from app.services.odoo.client import get_odoo_client
from app.services.cache.redis_client import get_redis_client

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
@router.get("/")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "task-management-agent",
    }


@router.get("/odoo")
async def odoo_health():
    """Check Odoo connection status."""
    client = get_odoo_client()
    status = client.check_connection()
    return {
        "service": "odoo",
        **status,
    }


@router.get("/redis")
async def redis_health():
    """Check Redis connection status."""
    client = await get_redis_client()
    status = await client.health_check()
    return {
        "service": "redis",
        **status,
    }


@router.get("/all")
async def full_health_check():
    """Comprehensive health check of all services."""
    odoo_client = get_odoo_client()
    odoo_status = odoo_client.check_connection()

    redis_client = await get_redis_client()
    redis_status = await redis_client.health_check()

    all_healthy = odoo_status.get("connected", False) and redis_status.get(
        "connected", False
    )

    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": {
            "odoo": odoo_status,
            "redis": redis_status,
        },
    }
