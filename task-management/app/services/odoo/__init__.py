"""Odoo integration services."""

from app.services.odoo.client import OdooClient
from app.services.odoo.task_service import OdooTaskService
from app.services.odoo.employee_service import OdooEmployeeService

__all__ = ["OdooClient", "OdooTaskService", "OdooEmployeeService"]
