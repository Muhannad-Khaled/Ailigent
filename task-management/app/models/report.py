"""Report-related Pydantic models."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProductivityMetrics(BaseModel):
    """Core productivity metrics."""

    period_start: str
    period_end: str
    total_created: int = 0
    completed: int = 0
    on_time: int = 0
    overdue: int = 0
    in_progress: int = 0
    completion_rate: float = 0
    on_time_rate: float = 0


class BottleneckInfo(BaseModel):
    """Information about an identified bottleneck."""

    type: str  # stage, employee, process, dependency
    location: str  # stage name, employee name, etc.
    severity: str  # critical, high, medium, low
    impact: str  # description of impact
    root_cause: str
    recommendation: str
    affected_tasks: int = 0


class StageMetrics(BaseModel):
    """Metrics for a task stage."""

    stage_id: int
    stage_name: str
    is_closed: bool = False
    task_count: int = 0
    percentage: float = 0
    avg_days_in_stage: Optional[float] = None
    overdue_in_stage: int = 0


class EmployeePerformanceMetrics(BaseModel):
    """Performance metrics for an employee."""

    employee_id: int
    employee_name: str
    tasks_completed: int = 0
    on_time_count: int = 0
    on_time_rate: float = 0
    average_completion_hours: float = 0
    productivity_score: float = 0


class ProductivityReport(BaseModel):
    """Comprehensive productivity report."""

    report_id: str
    report_type: str  # daily, weekly, monthly, custom
    period_start: str
    period_end: str
    generated_at: datetime = Field(default_factory=datetime.now)

    # Core metrics
    metrics: ProductivityMetrics

    # Stage analysis
    stage_metrics: List[StageMetrics] = Field(default_factory=list)

    # Team performance
    team_performance: List[EmployeePerformanceMetrics] = Field(default_factory=list)
    top_performers: List[str] = Field(default_factory=list)
    needs_improvement: List[str] = Field(default_factory=list)

    # AI insights
    insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)

    # Bottleneck analysis
    bottlenecks: List[BottleneckInfo] = Field(default_factory=list)

    # Summary
    executive_summary: str = ""


class ReportRequest(BaseModel):
    """Request parameters for generating a report."""

    report_type: str = "daily"  # daily, weekly, monthly, custom
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    include_ai_insights: bool = True
    employee_ids: Optional[List[int]] = None
    project_ids: Optional[List[int]] = None
    department_id: Optional[int] = None


class BottleneckAnalysisResponse(BaseModel):
    """Response for bottleneck analysis."""

    analysis_date: datetime = Field(default_factory=datetime.now)
    total_tasks_analyzed: int = 0
    bottlenecks: List[BottleneckInfo] = Field(default_factory=list)
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    priority_actions: List[str] = Field(default_factory=list)
    summary: str = ""


class AIRecommendation(BaseModel):
    """AI-generated recommendation."""

    category: str  # workload, process, assignment, timeline
    priority: str  # high, medium, low
    recommendation: str
    expected_impact: str
    implementation_effort: str  # low, medium, high
    affected_items: List[str] = Field(default_factory=list)
