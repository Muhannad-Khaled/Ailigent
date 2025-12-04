"""Dependency injection for FastAPI."""

from typing import Optional

from app.services.odoo.client import OdooClient, get_odoo_client
from app.services.odoo.task_service import OdooTaskService
from app.services.odoo.employee_service import OdooEmployeeService
from app.services.cache.redis_client import RedisClient, get_redis_client

# Global service instances
_task_service: Optional[OdooTaskService] = None
_employee_service: Optional[OdooEmployeeService] = None


def get_task_service() -> OdooTaskService:
    """Get or create task service instance."""
    global _task_service
    if _task_service is None:
        _task_service = OdooTaskService(get_odoo_client())
    return _task_service


def get_employee_service() -> OdooEmployeeService:
    """Get or create employee service instance."""
    global _employee_service
    if _employee_service is None:
        _employee_service = OdooEmployeeService(get_odoo_client())
    return _employee_service


async def get_redis() -> RedisClient:
    """Get Redis client instance."""
    return await get_redis_client()


def reset_services():
    """Reset service instances (useful for testing)."""
    global _task_service, _employee_service
    _task_service = None
    _employee_service = None
