"""Employee-related Pydantic models."""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class EmployeeBase(BaseModel):
    """Base employee model."""

    name: str
    email: Optional[str] = None
    department_id: Optional[int] = None
    job_title: Optional[str] = None


class EmployeeResponse(BaseModel):
    """Employee response model matching Odoo data."""

    id: int
    name: str
    user_id: Optional[Union[List[Any], bool]] = None
    work_email: Optional[Union[str, bool]] = None
    department_id: Optional[Union[List[Any], bool]] = None
    job_title: Optional[Union[str, bool]] = None
    parent_id: Optional[Union[List[Any], bool]] = None

    @property
    def department_name(self) -> Optional[str]:
        """Extract department name from department_id tuple."""
        if isinstance(self.department_id, list) and len(self.department_id) > 1:
            return self.department_id[1]
        return None

    @property
    def linked_user_id(self) -> Optional[int]:
        """Extract user ID from user_id tuple."""
        if isinstance(self.user_id, list) and len(self.user_id) > 0:
            return self.user_id[0]
        return None

    class Config:
        from_attributes = True


class EmployeeWorkload(BaseModel):
    """Detailed workload information for an employee."""

    employee_id: int
    employee_name: str
    user_id: Optional[int] = None
    email: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    total_tasks: int = 0
    total_planned_hours: float = 0
    total_remaining_hours: float = 0
    high_priority_count: int = 0
    blocked_count: int = 0
    overdue_count: int = 0
    weekly_capacity: float = 40.0
    utilization_percentage: float = 0
    status: str = "balanced"  # overloaded, balanced, underutilized
    tasks: List[Dict[str, Any]] = Field(default_factory=list)


class TeamWorkloadSummary(BaseModel):
    """Summary of team/department workload."""

    total_employees: int
    total_tasks: int
    total_remaining_hours: float = 0
    average_utilization: float = 0
    overloaded_count: int = 0
    underutilized_count: int = 0
    balanced_count: int = 0
    employees: List[Dict[str, Any]] = Field(default_factory=list)


class EmployeePerformance(BaseModel):
    """Employee performance metrics."""

    employee_id: int
    employee_name: str
    tasks_completed: int = 0
    tasks_assigned: int = 0
    on_time_rate: float = 0
    average_completion_hours: float = 0
    productivity_score: float = 0
    period_start: str
    period_end: str


class DepartmentResponse(BaseModel):
    """Department information."""

    id: int
    name: str
    manager_id: Optional[Union[List[Any], bool]] = None
    parent_id: Optional[Union[List[Any], bool]] = None

    @property
    def manager_name(self) -> Optional[str]:
        """Extract manager name from manager_id tuple."""
        if isinstance(self.manager_id, list) and len(self.manager_id) > 1:
            return self.manager_id[1]
        return None


class AvailableAssignee(BaseModel):
    """Employee available for task assignment."""

    employee_id: int
    employee_name: str
    user_id: int
    task_count: int
    remaining_hours: float
    utilization: float
    status: str
    high_priority: int = 0
    overdue: int = 0
