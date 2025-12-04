"""Appraisal Models."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AppraisalCycle(BaseModel):
    """Appraisal cycle model."""

    id: int
    name: str
    date_start: date
    date_end: date
    state: str
    total_appraisals: int = 0
    completed_appraisals: int = 0
    pending_appraisals: int = 0


class Appraisal(BaseModel):
    """Individual appraisal model."""

    id: int
    employee_id: int
    employee_name: str
    manager_id: Optional[int] = None
    manager_name: Optional[str] = None
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    date_close: Optional[date] = None
    state: str
    final_evaluation: Optional[str] = None
    create_date: Optional[datetime] = None


class AppraisalDetail(Appraisal):
    """Detailed appraisal with goals and notes."""

    goals: List["AppraisalGoal"] = []
    notes: List["AppraisalNote"] = []
    ai_summary: Optional[Dict[str, Any]] = None


class AppraisalGoal(BaseModel):
    """Appraisal goal model."""

    id: int
    name: str
    description: Optional[str] = None
    deadline: Optional[date] = None
    progression: int = 0
    employee_id: int
    employee_name: str


class AppraisalNote(BaseModel):
    """Appraisal feedback note."""

    id: int
    note: str
    author_id: int
    author_name: str
    date: datetime


class AppraisalSummary(BaseModel):
    """AI-generated appraisal summary."""

    executive_summary: str
    key_strengths: List[str]
    areas_for_improvement: List[str]
    goal_achievement: Dict[str, List[str]]
    themes: List[str]
    development_recommendations: List[str]
    overall_rating_suggestion: str
    action_items: List[str]


class AppraisalFilter(BaseModel):
    """Filter for appraisal queries."""

    employee_id: Optional[int] = None
    manager_id: Optional[int] = None
    department_id: Optional[int] = None
    state: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class ReminderStatus(BaseModel):
    """Status of reminder job."""

    last_run: Optional[datetime] = None
    reminders_sent: int = 0
    next_run: Optional[datetime] = None
    status: str


class SendRemindersRequest(BaseModel):
    """Request to manually send reminders."""

    appraisal_ids: Optional[List[int]] = Field(
        None, description="Specific appraisal IDs to remind, or None for all pending"
    )
    days_until_deadline: int = Field(
        default=7, ge=1, description="Send reminders for appraisals due within this many days"
    )


# Update forward references
AppraisalDetail.model_rebuild()
