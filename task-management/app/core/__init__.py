"""Core module - security, exceptions, and constants."""

from app.core.exceptions import (
    TaskManagementException,
    OdooConnectionError,
    OdooAuthenticationError,
    TaskNotFoundError,
    EmployeeNotFoundError,
    AIServiceError,
    NotificationError,
)
from app.core.security import verify_api_key

__all__ = [
    "TaskManagementException",
    "OdooConnectionError",
    "OdooAuthenticationError",
    "TaskNotFoundError",
    "EmployeeNotFoundError",
    "AIServiceError",
    "NotificationError",
    "verify_api_key",
]
