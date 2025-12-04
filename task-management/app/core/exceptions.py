"""Custom exceptions for Task Management Agent."""


class TaskManagementException(Exception):
    """Base exception for Task Management Agent."""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class OdooConnectionError(TaskManagementException):
    """Raised when unable to connect to Odoo."""

    pass


class OdooAuthenticationError(TaskManagementException):
    """Raised when Odoo authentication fails."""

    pass


class TaskNotFoundError(TaskManagementException):
    """Raised when a task is not found."""

    pass


class EmployeeNotFoundError(TaskManagementException):
    """Raised when an employee is not found."""

    pass


class AIServiceError(TaskManagementException):
    """Raised when AI service encounters an error."""

    pass


class NotificationError(TaskManagementException):
    """Raised when notification delivery fails."""

    pass


class CacheError(TaskManagementException):
    """Raised when cache operations fail."""

    pass


class ValidationError(TaskManagementException):
    """Raised when input validation fails."""

    pass
