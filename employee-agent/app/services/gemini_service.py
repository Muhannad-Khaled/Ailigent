"""
Backward compatibility module for GeminiService.

This module re-exports the LangChain-based implementation for backward compatibility.
New code should import from langchain_agent.py directly.
"""

# Re-export the LangChain-based agent as GeminiService for backward compatibility
from app.services.langchain_agent import (
    LangChainEmployeeAgent,
    LangChainEmployeeAgent as GeminiService,  # Main alias
    # Pydantic models
    EmployeeInfo,
    LeaveBalanceItem,
    LeaveRequestItem,
    PayslipItem,
    TaskItem,
)

__all__ = [
    "GeminiService",
    "LangChainEmployeeAgent",
    "EmployeeInfo",
    "LeaveBalanceItem",
    "LeaveRequestItem",
    "PayslipItem",
    "TaskItem",
]
