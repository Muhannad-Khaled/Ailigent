"""AI services using LangChain with Google Gemini."""

# Use LangChain-based client (backward compatible)
from app.services.ai.langchain_client import (
    LangChainTaskClient,
    GeminiClient,  # Alias for backward compatibility
    get_langchain_task_client,
    get_gemini_client,  # Alias for backward compatibility
    # Pydantic models
    WorkloadAnalysisResult,
    TaskAssignmentResult,
    BottleneckAnalysisResult,
    ProductivityReportResult,
    OverdueAnalysisResult,
)
from app.services.ai.workload_optimizer import WorkloadOptimizer
from app.services.ai.bottleneck_detector import BottleneckDetector
from app.services.ai.report_generator import AIReportGenerator

__all__ = [
    "LangChainTaskClient",
    "GeminiClient",
    "get_langchain_task_client",
    "get_gemini_client",
    "WorkloadOptimizer",
    "BottleneckDetector",
    "AIReportGenerator",
    "WorkloadAnalysisResult",
    "TaskAssignmentResult",
    "BottleneckAnalysisResult",
    "ProductivityReportResult",
    "OverdueAnalysisResult",
]
