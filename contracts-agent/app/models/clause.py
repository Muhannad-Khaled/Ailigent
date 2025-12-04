"""Clause Pydantic Models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ClauseType(str, Enum):
    """Clause type enumeration."""

    PAYMENT_TERMS = "payment_terms"
    DELIVERY = "delivery"
    WARRANTY = "warranty"
    LIABILITY = "liability"
    TERMINATION = "termination"
    CONFIDENTIALITY = "confidentiality"
    PENALTY = "penalty"
    RENEWAL = "renewal"
    FORCE_MAJEURE = "force_majeure"
    COMPLIANCE = "compliance"
    INDEMNIFICATION = "indemnification"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    DISPUTE_RESOLUTION = "dispute_resolution"
    GOVERNING_LAW = "governing_law"
    OTHER = "other"


class RiskLevel(str, Enum):
    """Risk level enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ClauseBase(BaseModel):
    """Base clause model."""

    contract_id: int = Field(..., description="Parent contract ID")
    clause_type: ClauseType = Field(..., description="Type of clause")
    title: str = Field(..., description="Clause title")
    content: str = Field(..., description="Full clause text")
    section_reference: Optional[str] = Field(None, description="Section reference (e.g., 'Section 5.2')")


class ClauseCreate(ClauseBase):
    """Model for creating a clause."""
    pass


class ClauseUpdate(BaseModel):
    """Model for updating a clause."""

    clause_type: Optional[ClauseType] = None
    title: Optional[str] = None
    content: Optional[str] = None
    section_reference: Optional[str] = None


class ClauseResponse(ClauseBase):
    """Model for clause responses."""

    id: int = Field(..., description="Clause ID")
    risk_level: Optional[RiskLevel] = Field(None, description="Assessed risk level")
    ai_analyzed: bool = Field(False, description="Whether AI analysis was performed")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Record last update timestamp")

    class Config:
        from_attributes = True


class ClauseAnalysis(BaseModel):
    """Model for AI clause analysis results."""

    clause_id: int = Field(..., description="Analyzed clause ID")
    risk_level: RiskLevel = Field(..., description="Assessed risk level")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    key_obligations: List[str] = Field(default_factory=list, description="Key obligations extracted")
    key_dates: List[Dict[str, Any]] = Field(default_factory=list, description="Important dates mentioned")
    financial_impact: Optional[str] = Field(None, description="Financial impact assessment")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for review")
    ai_confidence: float = Field(..., ge=0, le=1, description="AI confidence score (0-1)")
    analysis_timestamp: datetime = Field(..., description="When analysis was performed")


class ExtractedClause(BaseModel):
    """Model for AI-extracted clause."""

    clause_type: ClauseType
    title: str
    content: str
    section_reference: Optional[str] = None
    confidence: float = Field(..., ge=0, le=1, description="Extraction confidence")


class ClauseExtractionResult(BaseModel):
    """Model for clause extraction results."""

    contract_id: int
    document_id: int
    total_clauses: int
    clauses: List[ExtractedClause]
    extraction_timestamp: datetime
    processing_time_seconds: float
