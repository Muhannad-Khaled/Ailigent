"""Compliance Pydantic Models."""

from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ComplianceStatus(str, Enum):
    """Compliance status enumeration."""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING_REVIEW = "pending_review"
    EXEMPTED = "exempted"
    NOT_APPLICABLE = "not_applicable"


class ComplianceCategory(str, Enum):
    """Compliance category enumeration."""

    REGULATORY = "regulatory"
    CONTRACTUAL = "contractual"
    INTERNAL_POLICY = "internal_policy"
    INDUSTRY_STANDARD = "industry_standard"
    LEGAL = "legal"
    FINANCIAL = "financial"
    SECURITY = "security"
    ENVIRONMENTAL = "environmental"
    OTHER = "other"


class ComplianceBase(BaseModel):
    """Base compliance model."""

    contract_id: int = Field(..., description="Parent contract ID")
    category: ComplianceCategory = Field(..., description="Compliance category")
    requirement: str = Field(..., description="Compliance requirement description")
    due_date: Optional[date] = Field(None, description="Compliance due date")
    evidence_required: List[str] = Field(default_factory=list, description="Required evidence")


class ComplianceCreate(ComplianceBase):
    """Model for creating a compliance item."""
    pass


class ComplianceUpdate(BaseModel):
    """Model for updating a compliance item."""

    category: Optional[ComplianceCategory] = None
    requirement: Optional[str] = None
    status: Optional[ComplianceStatus] = None
    due_date: Optional[date] = None
    evidence_required: Optional[List[str]] = None
    evidence_provided: Optional[List[str]] = None
    review_date: Optional[date] = None
    reviewer_notes: Optional[str] = None


class ComplianceResponse(ComplianceBase):
    """Model for compliance item responses."""

    id: int = Field(..., description="Compliance item ID")
    status: ComplianceStatus = Field(..., description="Current status")
    evidence_provided: List[str] = Field(default_factory=list, description="Evidence provided")
    review_date: Optional[date] = Field(None, description="Last review date")
    reviewer_notes: Optional[str] = Field(None, description="Reviewer notes")
    contract_name: Optional[str] = Field(None, description="Parent contract name")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Record last update timestamp")

    class Config:
        from_attributes = True


class ComplianceSummary(BaseModel):
    """Model for compliance summary/list view."""

    id: int
    contract_id: int
    contract_name: Optional[str]
    category: ComplianceCategory
    requirement: str
    status: ComplianceStatus
    due_date: Optional[date]


class ComplianceListResponse(BaseModel):
    """Model for paginated compliance list response."""

    total: int
    page: int
    page_size: int
    items: List[ComplianceSummary]


class ComplianceFilter(BaseModel):
    """Model for compliance filtering."""

    contract_id: Optional[int] = None
    category: Optional[ComplianceCategory] = None
    status: Optional[ComplianceStatus] = None
    due_date_from: Optional[date] = None
    due_date_to: Optional[date] = None
    pending_only: bool = False
    non_compliant_only: bool = False


class ComplianceScore(BaseModel):
    """Model for compliance score."""

    contract_id: int
    contract_name: Optional[str]
    total_items: int
    compliant_items: int
    non_compliant_items: int
    pending_items: int
    exempted_items: int
    score: float = Field(..., ge=0, le=100, description="Compliance score (0-100)")
    calculated_at: datetime


class ComplianceReport(BaseModel):
    """Model for compliance report."""

    report_date: datetime
    total_contracts: int
    overall_compliance_score: float
    contracts_by_score: List[ComplianceScore]
    non_compliant_items: List[ComplianceSummary]
    pending_reviews: List[ComplianceSummary]
    upcoming_deadlines: List[ComplianceSummary]
