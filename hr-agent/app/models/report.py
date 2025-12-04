"""Report Models."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HeadcountReport(BaseModel):
    """Headcount report model."""

    report_date: date
    total_employees: int
    active_employees: int
    by_department: List[Dict[str, Any]]
    by_job_title: List[Dict[str, Any]]
    new_hires_this_month: int
    terminations_this_month: int
    net_change: int


class TurnoverReport(BaseModel):
    """Turnover analytics report."""

    period_start: date
    period_end: date
    total_terminations: int
    voluntary_terminations: int
    involuntary_terminations: int
    turnover_rate: float
    by_department: List[Dict[str, Any]]
    by_tenure: List[Dict[str, Any]]
    trends: List[Dict[str, Any]]


class DepartmentReport(BaseModel):
    """Department metrics report."""

    department_id: int
    department_name: str
    report_date: date
    headcount: int
    manager_name: Optional[str] = None
    avg_tenure_months: float
    new_hires_ytd: int
    terminations_ytd: int
    open_positions: int
    pending_leave_requests: int
    avg_attendance_rate: Optional[float] = None


class ReportInsights(BaseModel):
    """AI-generated insights for reports."""

    executive_summary: str
    key_insights: List[Dict[str, Any]]
    risks: List[Dict[str, Any]]
    opportunities: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    trends: Dict[str, List[str]]
    kpi_highlights: List[Dict[str, Any]]


class GenerateReportRequest(BaseModel):
    """Request to generate a custom report."""

    report_type: str = Field(
        ..., description="Type: headcount, turnover, department, attendance, leave_balance"
    )
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    department_ids: Optional[List[int]] = None
    include_ai_insights: bool = True


class ExportRequest(BaseModel):
    """Request to export a report."""

    format: str = Field(..., description="Export format: pdf or excel")
    include_charts: bool = True
    include_raw_data: bool = False


class ReportMetadata(BaseModel):
    """Metadata for a generated report."""

    id: str
    report_type: str
    generated_at: datetime
    generated_by: Optional[str] = None
    parameters: Dict[str, Any]
    status: str = "completed"
    file_path: Optional[str] = None


class ReportFilter(BaseModel):
    """Filter for listing reports."""

    report_type: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    status: Optional[str] = None
