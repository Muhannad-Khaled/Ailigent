"""Custom exceptions for HR Agent."""


class HRAgentException(Exception):
    """Base exception for HR Agent."""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class OdooConnectionError(HRAgentException):
    """Raised when unable to connect to Odoo."""

    pass


class OdooAuthenticationError(HRAgentException):
    """Raised when Odoo authentication fails."""

    pass


class OdooModuleNotFoundError(HRAgentException):
    """Raised when a required Odoo module is not installed."""

    pass


class ApplicantNotFoundError(HRAgentException):
    """Raised when an applicant is not found."""

    pass


class JobNotFoundError(HRAgentException):
    """Raised when a job position is not found."""

    pass


class AppraisalNotFoundError(HRAgentException):
    """Raised when an appraisal is not found."""

    pass


class EmployeeNotFoundError(HRAgentException):
    """Raised when an employee is not found."""

    pass


class LeaveRequestNotFoundError(HRAgentException):
    """Raised when a leave request is not found."""

    pass


class AIServiceError(HRAgentException):
    """Raised when AI service encounters an error."""

    pass


class DocumentParsingError(HRAgentException):
    """Raised when document parsing fails."""

    pass


class ReportGenerationError(HRAgentException):
    """Raised when report generation fails."""

    pass


class NotificationError(HRAgentException):
    """Raised when notification delivery fails."""

    pass


class CacheError(HRAgentException):
    """Raised when cache operations fail."""

    pass


class ValidationError(HRAgentException):
    """Raised when input validation fails."""

    pass


class IntegrationError(HRAgentException):
    """Raised when integration with other services fails."""

    pass
