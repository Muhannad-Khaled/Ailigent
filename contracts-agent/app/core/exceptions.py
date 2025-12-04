"""Custom exceptions for the Contracts Agent."""

from typing import Any, Dict, Optional


class ContractsAgentError(Exception):
    """Base exception for Contracts Agent."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class OdooConnectionError(ContractsAgentError):
    """Raised when unable to connect to Odoo."""
    pass


class OdooAuthenticationError(ContractsAgentError):
    """Raised when Odoo authentication fails."""
    pass


class OdooOperationError(ContractsAgentError):
    """Raised when an Odoo operation fails."""
    pass


class ContractNotFoundError(ContractsAgentError):
    """Raised when a contract is not found."""
    pass


class DocumentNotFoundError(ContractsAgentError):
    """Raised when a document/attachment is not found."""
    pass


class DocumentProcessingError(ContractsAgentError):
    """Raised when document processing fails (PDF/Word extraction)."""
    pass


class AIServiceError(ContractsAgentError):
    """Raised when AI service (Gemini) fails."""
    pass


class WebhookDeliveryError(ContractsAgentError):
    """Raised when webhook delivery fails."""
    pass


class ValidationError(ContractsAgentError):
    """Raised when validation fails."""
    pass
