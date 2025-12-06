"""AI services package."""

# Use LangChain-based client (backward compatible)
from .langchain_client import (
    LangChainContractClient,
    GeminiClient,  # Alias for backward compatibility
    get_langchain_client,
    get_gemini_client,  # Alias for backward compatibility
    # Pydantic models
    ContractAnalysisResult,
    ClauseExtractionResponse,
    ClauseRiskAnalysis,
    ExtractedClause,
)

__all__ = [
    "LangChainContractClient",
    "GeminiClient",
    "get_langchain_client",
    "get_gemini_client",
    "ContractAnalysisResult",
    "ClauseExtractionResponse",
    "ClauseRiskAnalysis",
    "ExtractedClause",
]
