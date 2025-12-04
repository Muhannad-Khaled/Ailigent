"""Recruitment API Endpoints."""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status

from app.models.applicant import (
    Applicant,
    ApplicantDetail,
    ApplicantFilter,
    CVAnalysisResult,
    CVUploadRequest,
    Interview,
    JobPosition,
    RankingResult,
    ScheduleInterviewRequest,
)
from app.models.common import PaginatedResponse
from app.services.odoo.recruitment_service import get_recruitment_service
from app.services.ai.gemini_client import get_gemini_client
from app.services.document.cv_parser import parse_cv_file
from app.core.exceptions import (
    ApplicantNotFoundError,
    JobNotFoundError,
    OdooModuleNotFoundError,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/jobs", response_model=List[JobPosition])
async def list_jobs(
    state: Optional[str] = Query(None, description="Filter by state: open, recruit, done"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
):
    """List open job positions."""
    service = get_recruitment_service()
    try:
        jobs = service.get_jobs(state=state, department_id=department_id)
        return jobs
    except OdooModuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message),
        )


@router.get("/jobs/{job_id}", response_model=JobPosition)
async def get_job(job_id: int):
    """Get job position details with requirements."""
    service = get_recruitment_service()
    try:
        job = service.get_job_by_id(job_id)
        if not job:
            raise JobNotFoundError(f"Job {job_id} not found")
        return job
    except JobNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.message))


@router.get("/applicants", response_model=PaginatedResponse)
async def list_applicants(
    job_id: Optional[int] = Query(None),
    stage_id: Optional[int] = Query(None),
    has_cv: Optional[bool] = Query(None),
    min_score: Optional[int] = Query(None, ge=0, le=100),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List applicants with filters."""
    service = get_recruitment_service()
    try:
        filters = ApplicantFilter(
            job_id=job_id,
            stage_id=stage_id,
            has_cv=has_cv,
            min_score=min_score,
            search=search,
        )
        result = service.get_applicants(filters, page=page, page_size=page_size)
        return result
    except OdooModuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message),
        )


@router.get("/applicants/{applicant_id}", response_model=ApplicantDetail)
async def get_applicant(applicant_id: int):
    """Get applicant details including CV analysis if available."""
    service = get_recruitment_service()
    try:
        applicant = service.get_applicant_by_id(applicant_id)
        if not applicant:
            raise ApplicantNotFoundError(f"Applicant {applicant_id} not found")
        return applicant
    except ApplicantNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.message))


@router.post("/applicants/upload")
async def upload_cv(
    job_id: int = Form(...),
    applicant_name: str = Form(...),
    email: str = Form(...),
    phone: Optional[str] = Form(None),
    cv_file: UploadFile = File(...),
):
    """Upload CV and create applicant."""
    # Validate file type
    if not cv_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file uploaded",
        )

    ext = cv_file.filename.split(".")[-1].lower()
    if ext not in ["pdf", "docx"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are allowed",
        )

    service = get_recruitment_service()
    try:
        # Read file content
        content = await cv_file.read()

        # Parse CV
        cv_text = await parse_cv_file(content, ext)

        # Create applicant with CV
        applicant = service.create_applicant(
            job_id=job_id,
            name=applicant_name,
            email=email,
            phone=phone,
            cv_content=content,
            cv_filename=cv_file.filename,
            cv_text=cv_text,
        )

        return {
            "success": True,
            "applicant_id": applicant["id"],
            "message": f"Applicant created successfully",
        }

    except OdooModuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message),
        )
    except Exception as e:
        logger.error(f"CV upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process CV: {str(e)}",
        )


@router.post("/applicants/{applicant_id}/analyze", response_model=CVAnalysisResult)
async def analyze_applicant_cv(applicant_id: int):
    """AI-analyze applicant's CV against job requirements."""
    service = get_recruitment_service()
    gemini = get_gemini_client()

    if not gemini.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not available",
        )

    try:
        # Get applicant and job info
        applicant = service.get_applicant_by_id(applicant_id)
        if not applicant:
            raise ApplicantNotFoundError(f"Applicant {applicant_id} not found")

        # Get CV text from cv_text or applicant_notes (Odoo 18 stores in applicant_notes)
        cv_text = applicant.get("cv_text") or applicant.get("applicant_notes")
        if not cv_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Applicant has no CV to analyze",
            )

        job = service.get_job_by_id(applicant["job_id"])
        job_requirements = f"{job.get('description', '')}\n\nRequirements:\n{job.get('requirements', '')}"

        # Analyze with AI
        analysis = await gemini.analyze_cv(
            cv_text=cv_text,
            job_requirements=job_requirements,
        )

        # Store analysis in Odoo (if supported)
        service.update_applicant_analysis(applicant_id, analysis)

        return analysis

    except ApplicantNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.message))


@router.post("/jobs/{job_id}/rank", response_model=RankingResult)
async def rank_candidates(job_id: int):
    """Rank all applicants for a job position using AI."""
    service = get_recruitment_service()
    gemini = get_gemini_client()

    if not gemini.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not available",
        )

    try:
        result = await service.rank_candidates_for_job(job_id)
        return result
    except JobNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.message))


@router.put("/applicants/{applicant_id}/stage")
async def update_applicant_stage(
    applicant_id: int,
    stage_id: int = Query(..., description="New stage ID"),
):
    """Update applicant's recruitment stage."""
    service = get_recruitment_service()
    try:
        result = service.update_applicant_stage(applicant_id, stage_id)
        return {"success": True, "message": "Stage updated successfully"}
    except ApplicantNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.message))


@router.get("/interviews", response_model=List[Interview])
async def list_interviews(
    applicant_id: Optional[int] = Query(None),
    from_date: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
):
    """List scheduled interviews."""
    service = get_recruitment_service()
    try:
        interviews = service.get_interviews(
            applicant_id=applicant_id,
            from_date=from_date,
            to_date=to_date,
        )
        return interviews
    except OdooModuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message),
        )


@router.post("/interviews/schedule", response_model=Interview)
async def schedule_interview(request: ScheduleInterviewRequest):
    """Schedule a new interview."""
    service = get_recruitment_service()
    try:
        interview = service.schedule_interview(
            applicant_id=request.applicant_id,
            start_datetime=request.start_datetime,
            duration_minutes=request.duration_minutes,
            interviewer_ids=request.interviewer_ids,
            location=request.location,
            notes=request.notes,
            send_notifications=request.send_notifications,
        )
        return interview
    except ApplicantNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.message))


@router.delete("/interviews/{interview_id}")
async def cancel_interview(interview_id: int):
    """Cancel an interview."""
    service = get_recruitment_service()
    try:
        service.cancel_interview(interview_id)
        return {"success": True, "message": "Interview cancelled"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview not found or already cancelled",
        )
