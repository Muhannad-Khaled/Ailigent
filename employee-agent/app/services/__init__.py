from .odoo_service import OdooService
# Use LangChain-based agent (backward compatible - exports GeminiService alias)
from .langchain_agent import LangChainEmployeeAgent, GeminiService
from .email_service import send_otp_email

__all__ = ["OdooService", "LangChainEmployeeAgent", "GeminiService", "send_otp_email"]
