"""
LangChain-based Task Management AI Client.

This module replaces the direct Google Gemini integration with LangChain,
providing structured output parsing with Pydantic models for task management analysis.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.config import settings
from app.core.exceptions import AIServiceError

logger = logging.getLogger(__name__)


# ==================== Pydantic Output Models ====================

class EmployeeWorkload(BaseModel):
    """Employee workload info"""
    id: int
    name: str
    utilization: float
    recommendation: str


class DeadlineRisk(BaseModel):
    """Deadline risk item"""
    task_id: int
    task_name: str
    risk_level: str = Field(description="high, medium, or low")
    reason: str


class WorkloadAnalysisResult(BaseModel):
    """Workload analysis result"""
    balance_score: float = Field(ge=0, le=100)
    summary: str
    overloaded_employees: List[EmployeeWorkload] = Field(default_factory=list)
    underutilized_employees: List[EmployeeWorkload] = Field(default_factory=list)
    deadline_risks: List[DeadlineRisk] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class AlternativeEmployee(BaseModel):
    """Alternative assignment option"""
    id: int
    name: str
    score: int = Field(ge=0, le=100)
    reason: str


class TaskAssignmentResult(BaseModel):
    """Task assignment recommendation"""
    recommended_employee_id: Optional[int] = Field(default=None)
    recommended_employee_name: Optional[str] = Field(default=None)
    confidence_score: int = Field(ge=0, le=100)
    reasoning: str
    alternatives: List[AlternativeEmployee] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class Bottleneck(BaseModel):
    """Single bottleneck item"""
    type: str = Field(description="stage, employee, process, or dependency")
    location: str
    severity: str = Field(description="critical, high, medium, or low")
    impact: str
    root_cause: str
    recommendation: str


class Pattern(BaseModel):
    """Workflow pattern"""
    pattern: str
    frequency: str
    impact: str


class BottleneckAnalysisResult(BaseModel):
    """Bottleneck analysis result"""
    bottlenecks: List[Bottleneck] = Field(default_factory=list)
    patterns: List[Pattern] = Field(default_factory=list)
    priority_actions: List[str] = Field(default_factory=list)
    summary: str = Field(default="")


class KeyMetrics(BaseModel):
    """Key productivity metrics"""
    overall_health: str = Field(description="healthy, warning, or critical")
    productivity_trend: str = Field(description="improving, stable, or declining")
    biggest_win: str
    biggest_concern: str


class TeamPerformance(BaseModel):
    """Team performance summary"""
    top_performers: List[str] = Field(default_factory=list)
    improvement_needed: List[str] = Field(default_factory=list)
    trend_analysis: str = Field(default="")


class ProductivityReportResult(BaseModel):
    """Productivity report result"""
    executive_summary: str
    key_metrics: KeyMetrics
    team_performance: TeamPerformance
    insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)


class RootCause(BaseModel):
    """Root cause analysis"""
    cause: str
    affected_tasks: int
    severity: str = Field(description="critical, high, medium, or low")


class EmployeePattern(BaseModel):
    """Employee overdue pattern"""
    employee_name: str
    overdue_count: int
    likely_reason: str
    recommendation: str


class OverdueAnalysisResult(BaseModel):
    """Overdue task analysis result"""
    analysis_summary: str
    root_causes: List[RootCause] = Field(default_factory=list)
    employee_patterns: List[EmployeePattern] = Field(default_factory=list)
    immediate_actions: List[str] = Field(default_factory=list)
    process_improvements: List[str] = Field(default_factory=list)


# ==================== LangChain Client ====================

class LangChainTaskClient:
    """
    LangChain-based wrapper for task management AI using Google Gemini.

    Features:
    - Workload analysis with structured output
    - Task assignment recommendations
    - Bottleneck detection
    - Productivity report generation
    """

    _instance: Optional["LangChainTaskClient"] = None

    def __new__(cls) -> "LangChainTaskClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not configured. AI features will be unavailable.")
            self.llm = None
        else:
            self.llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.3,
                max_output_tokens=4096,
            )

            self.llm_creative = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.7,
                max_output_tokens=2048,
            )

        self.model = settings.GEMINI_MODEL
        self._initialized = True
        logger.info(f"LangChainTaskClient initialized with model: {self.model}")

    def is_available(self) -> bool:
        """Check if LangChain client is available."""
        return self.llm is not None

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_instruction: Optional[str] = None,
    ) -> str:
        """Generate text completion using LangChain."""
        if not self.llm:
            raise AIServiceError(
                "LangChain client not initialized. Check GEMINI_API_KEY configuration."
            )

        try:
            messages = []
            if system_instruction:
                messages.append(SystemMessage(content=system_instruction))
            messages.append(HumanMessage(content=prompt))

            llm = self.llm_creative if temperature >= 0.5 else self.llm
            response = await llm.ainvoke(messages)
            return response.content

        except Exception as e:
            logger.error(f"LangChain generation error: {e}")
            raise AIServiceError(
                "Failed to generate AI response",
                details={"error": str(e)},
            )

    async def analyze_json(
        self,
        prompt: str,
        data: Dict[str, Any],
        system_instruction: str,
    ) -> Dict[str, Any]:
        """Generate structured JSON response."""
        if not self.llm:
            raise AIServiceError(
                "LangChain client not initialized. Check GEMINI_API_KEY configuration."
            )

        full_prompt = f"{prompt}\n\nData to analyze:\n```json\n{json.dumps(data, indent=2, default=str)}\n```"

        full_instruction = (
            f"{system_instruction}\n\n"
            "IMPORTANT: Respond ONLY with valid JSON. "
            "Do not include any markdown formatting, code blocks, or explanatory text. "
            "Your entire response must be parseable as JSON."
        )

        response = await self.generate(
            prompt=full_prompt,
            system_instruction=full_instruction,
            temperature=0.3,
        )

        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(
                    line for line in lines
                    if not line.strip().startswith("```")
                )

            return json.loads(cleaned)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {response[:500]}")
            raise AIServiceError(
                "AI response was not valid JSON",
                details={"error": str(e), "response_preview": response[:200]},
            )

    async def analyze_workload_structured(
        self,
        employees: List[Dict],
        tasks: List[Dict],
        weekly_capacity: float = 40.0,
    ) -> WorkloadAnalysisResult:
        """Analyze team workload with structured output."""
        if not self.llm:
            raise AIServiceError("LangChain client not initialized.")

        parser = PydanticOutputParser(pydantic_object=WorkloadAnalysisResult)

        data = {
            "employees": employees,
            "tasks_summary": {
                "total_count": len(tasks),
                "high_priority_count": sum(1 for t in tasks if t.get("priority") in ("2", "3")),
                "overdue_count": sum(1 for t in tasks if t.get("days_overdue", 0) > 0),
            },
            "weekly_capacity": weekly_capacity,
        }

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a workload analysis expert. Analyze the team capacity
and provide actionable insights. Focus on practical recommendations.

{format_instructions}"""),
            ("human", """Analyze the team workload distribution.

Evaluate:
1. Overall workload balance across the team (0-100 score)
2. Identify overloaded employees (>80% utilization)
3. Identify underutilized employees (<50% utilization)
4. Check for deadline conflicts and risks

Data:
{data}"""),
        ])

        try:
            chain = prompt | self.llm | parser
            return await chain.ainvoke({
                "data": json.dumps(data, indent=2, default=str),
                "format_instructions": parser.get_format_instructions(),
            })
        except Exception as e:
            logger.error(f"Structured workload analysis failed: {e}")
            raise AIServiceError(
                "Failed to analyze workload",
                details={"error": str(e)},
            )

    async def recommend_assignment_structured(
        self,
        task: Dict,
        available_employees: List[Dict],
    ) -> TaskAssignmentResult:
        """Recommend task assignment with structured output."""
        if not self.llm:
            raise AIServiceError("LangChain client not initialized.")

        parser = PydanticOutputParser(pydantic_object=TaskAssignmentResult)

        data = {
            "task": task,
            "candidates": available_employees[:10],
        }

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a task assignment optimizer. Recommend the best employee
based on their current workload, capacity, and the task requirements.
Prioritize balanced workload distribution.

{format_instructions}"""),
            ("human", """Recommend the best employee assignment for this task.

Consider:
1. Current workload and remaining capacity (most important)
2. Skills match with task requirements
3. Deadline urgency
4. Historical completion rate

Data:
{data}"""),
        ])

        try:
            chain = prompt | self.llm | parser
            return await chain.ainvoke({
                "data": json.dumps(data, indent=2, default=str),
                "format_instructions": parser.get_format_instructions(),
            })
        except Exception as e:
            logger.error(f"Structured assignment recommendation failed: {e}")
            raise AIServiceError(
                "Failed to recommend assignment",
                details={"error": str(e)},
            )

    async def detect_bottlenecks_structured(
        self,
        workflow_data: Dict,
    ) -> BottleneckAnalysisResult:
        """Detect workflow bottlenecks with structured output."""
        if not self.llm:
            raise AIServiceError("LangChain client not initialized.")

        parser = PydanticOutputParser(pydantic_object=BottleneckAnalysisResult)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a workflow optimization expert. Identify bottlenecks
and blockers in the task management workflow.

{format_instructions}"""),
            ("human", """Analyze the workflow data to identify bottlenecks.

Identify:
1. Stages where tasks accumulate (stage bottlenecks)
2. Employees who are blocking points (capacity bottlenecks)
3. Common patterns in delays
4. Root causes of overdue tasks

Data:
{data}"""),
        ])

        try:
            chain = prompt | self.llm | parser
            return await chain.ainvoke({
                "data": json.dumps(workflow_data, indent=2, default=str),
                "format_instructions": parser.get_format_instructions(),
            })
        except Exception as e:
            logger.error(f"Structured bottleneck detection failed: {e}")
            raise AIServiceError(
                "Failed to detect bottlenecks",
                details={"error": str(e)},
            )

    async def generate_productivity_report_structured(
        self,
        metrics: Dict,
    ) -> ProductivityReportResult:
        """Generate productivity report with structured output."""
        if not self.llm:
            raise AIServiceError("LangChain client not initialized.")

        parser = PydanticOutputParser(pydantic_object=ProductivityReportResult)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a productivity analytics expert. Generate comprehensive
reports with actionable insights.

{format_instructions}"""),
            ("human", """Generate a comprehensive productivity report.

Include analysis of:
1. Task completion rates and trends
2. Team and individual performance
3. Time management and deadline adherence
4. Areas of improvement

Metrics:
{metrics}"""),
        ])

        try:
            chain = prompt | self.llm | parser
            return await chain.ainvoke({
                "metrics": json.dumps(metrics, indent=2, default=str),
                "format_instructions": parser.get_format_instructions(),
            })
        except Exception as e:
            logger.error(f"Structured productivity report failed: {e}")
            raise AIServiceError(
                "Failed to generate productivity report",
                details={"error": str(e)},
            )

    async def analyze_overdue_tasks_structured(
        self,
        overdue_data: Dict,
    ) -> OverdueAnalysisResult:
        """Analyze overdue tasks with structured output."""
        if not self.llm:
            raise AIServiceError("LangChain client not initialized.")

        parser = PydanticOutputParser(pydantic_object=OverdueAnalysisResult)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a task management expert. Analyze overdue tasks
and provide actionable insights for improvement.

{format_instructions}"""),
            ("human", """Analyze the overdue tasks and provide actionable insights.

Consider:
1. Patterns in why tasks are overdue
2. Common blockers
3. Employee-specific issues
4. Process improvements needed

Data:
{data}"""),
        ])

        try:
            chain = prompt | self.llm | parser
            return await chain.ainvoke({
                "data": json.dumps(overdue_data, indent=2, default=str),
                "format_instructions": parser.get_format_instructions(),
            })
        except Exception as e:
            logger.error(f"Structured overdue analysis failed: {e}")
            raise AIServiceError(
                "Failed to analyze overdue tasks",
                details={"error": str(e)},
            )

    async def health_check(self) -> Dict[str, Any]:
        """Check LangChain/Gemini API connectivity."""
        if not self.llm:
            return {
                "available": False,
                "error": "Client not initialized",
            }

        try:
            response = await self.generate(
                prompt="Respond with only: OK",
                max_tokens=10,
                temperature=0,
            )

            return {
                "available": True,
                "model": self.model,
                "framework": "langchain",
                "test_response": response.strip(),
            }

        except Exception as e:
            return {
                "available": False,
                "error": str(e),
            }


# ==================== Singleton Access ====================

_langchain_client: Optional[LangChainTaskClient] = None


def get_langchain_task_client() -> LangChainTaskClient:
    """Get the singleton LangChain task client instance."""
    global _langchain_client
    if _langchain_client is None:
        _langchain_client = LangChainTaskClient()
    return _langchain_client


# ==================== Backward Compatibility Aliases ====================
GeminiClient = LangChainTaskClient
get_gemini_client = get_langchain_task_client
