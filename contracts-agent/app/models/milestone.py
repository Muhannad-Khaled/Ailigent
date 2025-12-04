"""Milestone Pydantic Models."""

from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class MilestoneStatus(str, Enum):
    """Milestone status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    AT_RISK = "at_risk"
    CANCELLED = "cancelled"


class ResponsibleParty(str, Enum):
    """Responsible party enumeration."""

    US = "us"
    PARTNER = "partner"
    BOTH = "both"


class MilestoneBase(BaseModel):
    """Base milestone model."""

    contract_id: int = Field(..., description="Parent contract ID")
    name: str = Field(..., description="Milestone name")
    description: Optional[str] = Field(None, description="Milestone description")
    due_date: date = Field(..., description="Due date")
    deliverables: List[str] = Field(default_factory=list, description="List of deliverables")
    responsible_party: ResponsibleParty = Field(..., description="Who is responsible")
    value: Optional[float] = Field(None, description="Associated payment/value")


class MilestoneCreate(MilestoneBase):
    """Model for creating a milestone."""
    pass


class MilestoneUpdate(BaseModel):
    """Model for updating a milestone."""

    name: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    deliverables: Optional[List[str]] = None
    responsible_party: Optional[ResponsibleParty] = None
    value: Optional[float] = None
    status: Optional[MilestoneStatus] = None
    completion_date: Optional[date] = None
    notes: Optional[str] = None


class MilestoneResponse(MilestoneBase):
    """Model for milestone responses."""

    id: int = Field(..., description="Milestone ID")
    status: MilestoneStatus = Field(..., description="Current status")
    days_until_due: Optional[int] = Field(None, description="Days until due (negative if overdue)")
    completion_date: Optional[date] = Field(None, description="Actual completion date")
    notes: Optional[str] = Field(None, description="Additional notes")
    contract_name: Optional[str] = Field(None, description="Parent contract name")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Record last update timestamp")

    class Config:
        from_attributes = True


class MilestoneSummary(BaseModel):
    """Model for milestone summary/list view."""

    id: int
    name: str
    contract_id: int
    contract_name: Optional[str]
    due_date: date
    status: MilestoneStatus
    days_until_due: Optional[int]
    responsible_party: ResponsibleParty
    value: Optional[float]


class MilestoneListResponse(BaseModel):
    """Model for paginated milestone list response."""

    total: int
    page: int
    page_size: int
    milestones: List[MilestoneSummary]


class MilestoneFilter(BaseModel):
    """Model for milestone filtering."""

    contract_id: Optional[int] = None
    status: Optional[MilestoneStatus] = None
    responsible_party: Optional[ResponsibleParty] = None
    due_date_from: Optional[date] = None
    due_date_to: Optional[date] = None
    overdue_only: bool = False
    upcoming_days: Optional[int] = None
