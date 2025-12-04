"""Contract Pydantic Models."""

from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ContractStatus(str, Enum):
    """Contract status enumeration."""

    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRING_SOON = "expiring_soon"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    RENEWED = "renewed"


class ContractType(str, Enum):
    """Contract type enumeration."""

    SERVICE = "service"
    PURCHASE = "purchase"
    SALES = "sales"
    NDA = "nda"
    EMPLOYMENT = "employment"
    LEASE = "lease"
    MAINTENANCE = "maintenance"
    CONSULTING = "consulting"
    OTHER = "other"


class ContractBase(BaseModel):
    """Base contract model with common fields."""

    name: str = Field(..., description="Contract name/title")
    contract_type: ContractType = Field(..., description="Type of contract")
    partner_id: int = Field(..., description="Odoo partner ID (vendor/customer)")
    partner_name: Optional[str] = Field(None, description="Partner name")
    start_date: date = Field(..., description="Contract start date")
    end_date: date = Field(..., description="Contract end date")
    value: Optional[float] = Field(None, description="Contract total value")
    currency: str = Field("USD", description="Currency code")
    description: Optional[str] = Field(None, description="Contract description")
    project_ids: List[int] = Field(default_factory=list, description="Linked Odoo project IDs")


class ContractCreate(ContractBase):
    """Model for creating a new contract."""

    document_ids: List[int] = Field(
        default_factory=list,
        description="Odoo attachment IDs for contract documents"
    )


class ContractUpdate(BaseModel):
    """Model for updating a contract."""

    name: Optional[str] = None
    contract_type: Optional[ContractType] = None
    partner_id: Optional[int] = None
    partner_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    value: Optional[float] = None
    currency: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ContractStatus] = None
    project_ids: Optional[List[int]] = None
    document_ids: Optional[List[int]] = None


class ContractResponse(ContractBase):
    """Model for contract responses."""

    id: int = Field(..., description="Contract ID")
    status: ContractStatus = Field(..., description="Current contract status")
    days_until_expiry: Optional[int] = Field(None, description="Days until contract expires")
    compliance_score: Optional[float] = Field(None, description="Compliance score (0-100)")
    clause_count: int = Field(0, description="Number of extracted clauses")
    milestone_count: int = Field(0, description="Number of milestones")
    active_alerts: int = Field(0, description="Number of active alerts")
    document_ids: List[int] = Field(default_factory=list, description="Attached document IDs")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Record last update timestamp")

    class Config:
        from_attributes = True


class ContractSummary(BaseModel):
    """Model for contract summary/list view."""

    id: int
    name: str
    contract_type: ContractType
    partner_name: Optional[str]
    status: ContractStatus
    start_date: date
    end_date: date
    value: Optional[float]
    currency: str
    days_until_expiry: Optional[int]
    compliance_score: Optional[float]


class ContractListResponse(BaseModel):
    """Model for paginated contract list response."""

    total: int = Field(..., description="Total number of contracts")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    contracts: List[ContractSummary] = Field(..., description="List of contracts")


class ContractFilter(BaseModel):
    """Model for contract filtering."""

    status: Optional[ContractStatus] = None
    contract_type: Optional[ContractType] = None
    partner_id: Optional[int] = None
    start_date_from: Optional[date] = None
    start_date_to: Optional[date] = None
    end_date_from: Optional[date] = None
    end_date_to: Optional[date] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    expiring_in_days: Optional[int] = None
    search: Optional[str] = None
