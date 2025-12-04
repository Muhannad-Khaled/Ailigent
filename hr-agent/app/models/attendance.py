"""Attendance and Leave Models."""

from datetime import date, datetime, time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LeaveRequest(BaseModel):
    """Leave request model."""

    id: int
    employee_id: int
    employee_name: str
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    leave_type_id: int
    leave_type_name: str
    date_from: datetime
    date_to: datetime
    number_of_days: float
    state: str
    request_date: Optional[datetime] = None
    notes: Optional[str] = None


class LeaveBalance(BaseModel):
    """Employee leave balance."""

    employee_id: int
    employee_name: str
    leave_type_id: int
    leave_type_name: str
    allocated_days: float
    taken_days: float
    remaining_days: float


class LeaveBalanceReport(BaseModel):
    """Department leave balance report."""

    department_id: int
    department_name: str
    report_date: date
    balances: List[LeaveBalance]
    total_pending_requests: int


class AttendanceRecord(BaseModel):
    """Attendance record model."""

    id: int
    employee_id: int
    employee_name: str
    check_in: datetime
    check_out: Optional[datetime] = None
    worked_hours: float = 0


class AttendanceSummary(BaseModel):
    """Organization-wide attendance summary."""

    date: date
    total_employees: int
    present_count: int
    absent_count: int
    on_leave_count: int
    attendance_rate: float
    avg_work_hours: float
    late_arrivals: int
    early_departures: int


class DepartmentAttendance(BaseModel):
    """Department attendance summary."""

    department_id: int
    department_name: str
    date: date
    total_employees: int
    present_count: int
    absent_count: int
    on_leave_count: int
    attendance_rate: float


class AttendanceAnomaly(BaseModel):
    """Detected attendance anomaly."""

    employee_id: int
    employee_name: str
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    anomaly_type: str
    severity: str
    description: str
    frequency: str
    dates_affected: List[str]
    recommendation: str


class AttendanceAnomalyReport(BaseModel):
    """Full anomaly detection report."""

    analysis_date: date
    period_start: date
    period_end: date
    anomalies: List[AttendanceAnomaly]
    summary: Dict[str, Any]
    department_patterns: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    overall_assessment: str


class LeaveApprovalRequest(BaseModel):
    """Request to approve/reject leave."""

    notes: Optional[str] = Field(None, description="Approval/rejection notes")


class LeaveRequestCreate(BaseModel):
    """Request to create a new leave request."""

    employee_id: int = Field(..., description="Employee ID")
    leave_type_id: int = Field(..., description="Leave type ID (1=Annual, 2=Sick, etc.)")
    date_from: date = Field(..., description="Start date of leave")
    date_to: date = Field(..., description="End date of leave")
    notes: Optional[str] = Field(None, description="Leave request notes/reason")


class AttendanceFilter(BaseModel):
    """Filter for attendance queries."""

    employee_id: Optional[int] = None
    department_id: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class LeaveFilter(BaseModel):
    """Filter for leave queries."""

    employee_id: Optional[int] = None
    department_id: Optional[int] = None
    leave_type_id: Optional[int] = None
    state: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class MonthlyAttendanceReport(BaseModel):
    """Monthly attendance report."""

    year: int
    month: int
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    total_working_days: int
    summary: Dict[str, Any]
    by_employee: List[Dict[str, Any]]
    trends: List[Dict[str, Any]]
