"""Report Pydantic Models."""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.contract import ContractStatus, ContractType
from app.models.clause import RiskLevel


class ReportType(str, Enum):
    """Report type enumeration."""

    PORTFOLIO = "portfolio"
    EXPIRY = "expiry"
    COMPLIANCE = "compliance"
    FINANCIAL = "financial"
    RISK = "risk"
    CONTRACT_STATUS = "contract_status"


class PortfolioMetrics(BaseModel):
    """Model for portfolio metrics."""

    total_contracts: int
    active_contracts: int
    expiring_soon: int
    expired: int
    total_value: float
    currency: str
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    average_compliance_score: float


class ExpiryTimeline(BaseModel):
    """Model for expiry timeline item."""

    contract_id: int
    contract_name: str
    partner_name: Optional[str]
    expiry_date: date
    days_until_expiry: int
    value: Optional[float]
    currency: str
    status: ContractStatus


class PortfolioReport(BaseModel):
    """Model for portfolio overview report."""

    report_type: str = "portfolio"
    generated_at: datetime
    period_start: Optional[date]
    period_end: Optional[date]
    metrics: PortfolioMetrics
    recent_changes: List[Dict[str, Any]]
    recommendations: List[str]


class ExpiryReport(BaseModel):
    """Model for expiry timeline report."""

    report_type: str = "expiry"
    generated_at: datetime
    contracts_expiring_30_days: List[ExpiryTimeline]
    contracts_expiring_60_days: List[ExpiryTimeline]
    contracts_expiring_90_days: List[ExpiryTimeline]
    total_value_at_risk: float
    currency: str
    recommendations: List[str]


class FinancialSummary(BaseModel):
    """Model for financial summary."""

    contract_id: int
    contract_name: str
    contract_type: ContractType
    total_value: float
    currency: str
    payments_made: float
    payments_pending: float
    next_payment_date: Optional[date]
    next_payment_amount: Optional[float]


class FinancialReport(BaseModel):
    """Model for financial obligations report."""

    report_type: str = "financial"
    generated_at: datetime
    period_start: date
    period_end: date
    total_obligations: float
    currency: str
    by_contract_type: Dict[str, float]
    contracts: List[FinancialSummary]
    upcoming_payments: List[Dict[str, Any]]


class RiskSummary(BaseModel):
    """Model for risk summary per contract."""

    contract_id: int
    contract_name: str
    overall_risk_level: RiskLevel
    high_risk_clauses: int
    critical_clauses: int
    compliance_issues: int
    overdue_milestones: int
    risk_factors: List[str]


class RiskReport(BaseModel):
    """Model for risk analysis report."""

    report_type: str = "risk"
    generated_at: datetime
    overall_risk_assessment: str
    contracts_by_risk_level: Dict[str, int]
    high_risk_contracts: List[RiskSummary]
    critical_issues: List[Dict[str, Any]]
    recommendations: List[str]


class ContractStatusReport(BaseModel):
    """Model for single contract status report."""

    report_type: str = "contract_status"
    generated_at: datetime
    contract_id: int
    contract_name: str
    contract_type: ContractType
    status: ContractStatus
    partner_name: Optional[str]
    start_date: date
    end_date: date
    days_until_expiry: Optional[int]
    value: Optional[float]
    currency: str
    compliance_score: Optional[float]
    milestones_summary: Dict[str, int]
    compliance_summary: Dict[str, int]
    risk_assessment: Optional[RiskSummary]
    ai_summary: Optional[str]
    recommendations: List[str]


class ReportRequest(BaseModel):
    """Model for report generation request."""

    report_type: ReportType
    contract_id: Optional[int] = None  # For single contract reports
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    include_ai_analysis: bool = True
    format: str = "json"  # json, pdf, excel
