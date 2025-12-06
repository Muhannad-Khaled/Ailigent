"""AI services package."""

# Use LangChain-based client (backward compatible)
from .langchain_client import (
    LangChainHRClient,
    GeminiClient,  # Alias for backward compatibility
    get_langchain_hr_client,
    get_gemini_client,  # Alias for backward compatibility
    # Pydantic models
    CVAnalysisResult,
    AppraisalSummaryResult,
    HRInsightsResult,
    AttendanceAnomalyResult,
    CandidateRankingResult,
)

__all__ = [
    "LangChainHRClient",
    "GeminiClient",
    "get_langchain_hr_client",
    "get_gemini_client",
    "CVAnalysisResult",
    "AppraisalSummaryResult",
    "HRInsightsResult",
    "AttendanceAnomalyResult",
    "CandidateRankingResult",
]
