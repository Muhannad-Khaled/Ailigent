"""Applicant/Recruitment Models."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class JobPosition(BaseModel):
    """Job position model."""

    id: int
    name: str
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    no_of_recruitment: int = 0
    no_of_hired_employee: int = 0
    state: str = "open"

    @field_validator("description", "requirements", mode="before")
    @classmethod
    def convert_false_to_none(cls, v):
        """Odoo returns False for empty text fields instead of None."""
        if v is False:
            return None
        return v


class Applicant(BaseModel):
    """Job applicant model."""

    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    job_id: Optional[int] = None
    job_name: Optional[str] = None
    stage_id: Optional[int] = None
    stage_name: Optional[str] = None
    priority: str = "0"
    create_date: Optional[datetime] = None
    cv_attached: bool = False


class ApplicantDetail(Applicant):
    """Detailed applicant model with CV analysis."""

    linkedin_profile: Optional[str] = None
    source: Optional[str] = None
    medium: Optional[str] = None
    cv_text: Optional[str] = None
    ai_score: Optional[int] = None
    ai_analysis: Optional[Dict[str, Any]] = None


class CVUploadRequest(BaseModel):
    """CV upload request."""

    job_id: int = Field(..., description="Job position ID")
    applicant_name: str = Field(..., description="Applicant's full name")
    email: str = Field(..., description="Applicant's email")
    phone: Optional[str] = Field(None, description="Applicant's phone number")


class CVAnalysisResult(BaseModel):
    """CV analysis result from AI."""

    overall_score: int = Field(..., ge=0, le=100)
    skill_match: Dict[str, List[str]]
    experience_analysis: Dict[str, Any]
    education_match: Dict[str, Any]
    strengths: List[str]
    concerns: List[str]
    interview_questions: List[str]
    hiring_recommendation: str
    summary: str


class CandidateRanking(BaseModel):
    """Candidate ranking result."""

    rank: int
    applicant_id: int
    name: str
    overall_score: int
    strengths: List[str]
    concerns: List[str]
    recommendation: str


class RankingResult(BaseModel):
    """Full ranking result for a job."""

    job_id: int
    job_name: str
    rankings: List[CandidateRanking]
    comparison_notes: str
    top_pick_rationale: str


class Interview(BaseModel):
    """Interview model."""

    id: int
    applicant_id: int
    applicant_name: str
    job_id: Optional[int] = None
    job_name: Optional[str] = None
    start_datetime: datetime
    end_datetime: datetime
    interviewer_ids: List[int] = []
    interviewer_names: List[str] = []
    location: Optional[str] = None
    notes: Optional[str] = None
    status: str = "scheduled"


class ScheduleInterviewRequest(BaseModel):
    """Request to schedule an interview."""

    applicant_id: int = Field(..., description="Applicant ID")
    start_datetime: datetime = Field(..., description="Interview start time")
    duration_minutes: int = Field(default=60, ge=15, le=240, description="Interview duration")
    interviewer_ids: List[int] = Field(..., description="List of interviewer employee IDs")
    location: Optional[str] = Field(None, description="Interview location or video link")
    notes: Optional[str] = Field(None, description="Interview notes/agenda")
    send_notifications: bool = Field(default=True, description="Send email notifications")


class ApplicantFilter(BaseModel):
    """Filter for applicant queries."""

    job_id: Optional[int] = None
    stage_id: Optional[int] = None
    priority: Optional[str] = None
    has_cv: Optional[bool] = None
    min_score: Optional[int] = None
    search: Optional[str] = None
