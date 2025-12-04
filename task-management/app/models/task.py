"""Task-related Pydantic models."""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "0"
    NORMAL = "1"
    HIGH = "2"
    URGENT = "3"


class KanbanState(str, Enum):
    """Kanban card states."""

    NORMAL = "normal"
    DONE = "done"
    BLOCKED = "blocked"


class TaskBase(BaseModel):
    """Base task model with common fields."""

    name: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    project_id: Optional[int] = None
    planned_hours: Optional[float] = Field(default=0, ge=0)
    priority: TaskPriority = TaskPriority.NORMAL
    date_deadline: Optional[date] = None
    tag_ids: List[int] = Field(default_factory=list)


class TaskCreate(TaskBase):
    """Model for creating a new task."""

    user_ids: List[int] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    """Model for updating an existing task."""

    name: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    planned_hours: Optional[float] = Field(None, ge=0)
    priority: Optional[TaskPriority] = None
    date_deadline: Optional[date] = None
    user_ids: Optional[List[int]] = None
    stage_id: Optional[int] = None
    kanban_state: Optional[KanbanState] = None


class TaskResponse(BaseModel):
    """Task response model matching Odoo data."""

    id: int
    name: str
    project_id: Optional[Union[List[Any], bool]] = None
    user_ids: List[int] = Field(default_factory=list)
    stage_id: Optional[Union[List[Any], bool]] = None
    date_deadline: Optional[str] = None
    date_assign: Optional[str] = None
    priority: str = "1"
    tag_ids: List[int] = Field(default_factory=list)
    # Note: planned_hours/effective_hours/remaining_hours require hr_timesheet module
    # allocated_hours is available in base Odoo 18 project module
    planned_hours: Optional[float] = None
    effective_hours: Optional[float] = None
    remaining_hours: Optional[float] = None
    allocated_hours: Optional[float] = None
    kanban_state: Optional[str] = None
    description: Optional[Union[str, bool]] = None
    create_date: Optional[str] = None
    write_date: Optional[str] = None
    parent_id: Optional[Union[List[Any], bool]] = None
    child_ids: List[int] = Field(default_factory=list)
    date_last_stage_update: Optional[str] = None
    state: Optional[str] = None

    @field_validator("date_deadline", "date_assign", "create_date", "write_date", "date_last_stage_update", "kanban_state", "state", mode="before")
    @classmethod
    def convert_false_to_none(cls, v):
        """Odoo returns False for empty fields instead of None."""
        if v is False:
            return None
        return v

    @property
    def project_name(self) -> Optional[str]:
        """Extract project name from project_id tuple."""
        if isinstance(self.project_id, list) and len(self.project_id) > 1:
            return self.project_id[1]
        return None

    @property
    def stage_name(self) -> Optional[str]:
        """Extract stage name from stage_id tuple."""
        if isinstance(self.stage_id, list) and len(self.stage_id) > 1:
            return self.stage_id[1]
        return None

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Paginated list of tasks."""

    tasks: List[TaskResponse]
    total: int
    page: int = 1
    page_size: int = 100


class TaskAssignRequest(BaseModel):
    """Request model for task assignment."""

    user_ids: List[int] = Field(..., min_length=1)


class OverdueTasksResponse(BaseModel):
    """Response containing overdue tasks."""

    tasks: List[TaskResponse]
    count: int


class WorkloadResponse(BaseModel):
    """Workload information for a user."""

    user_id: int
    total_tasks: int
    total_planned_hours: float
    total_remaining_hours: float
    high_priority_count: int
    blocked_count: int = 0
    overdue_count: int = 0
    utilization_percentage: Optional[float] = None
    status: Optional[str] = None
    tasks: List[Dict[str, Any]] = Field(default_factory=list)


class TaskDistributionRecommendation(BaseModel):
    """AI recommendation for task assignment."""

    task_id: int
    task_name: str
    recommended_user_id: int
    recommended_user_name: str
    confidence_score: float = Field(ge=0, le=100)
    reasoning: str
    alternatives: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class WorkloadBalanceAnalysis(BaseModel):
    """Analysis of team workload balance."""

    balance_score: float = Field(ge=0, le=100)
    summary: str
    overloaded_employees: List[Dict[str, Any]]
    underutilized_employees: List[Dict[str, Any]]
    recommendations: List[str]
    deadline_risks: List[Dict[str, Any]] = Field(default_factory=list)
