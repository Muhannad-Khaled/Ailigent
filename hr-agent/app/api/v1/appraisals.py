"""Appraisals API Endpoints."""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.models.appraisal import (
    Appraisal,
    AppraisalCycle,
    AppraisalDetail,
    AppraisalFilter,
    AppraisalSummary,
    ReminderStatus,
    SendRemindersRequest,
)
from app.models.common import PaginatedResponse
from app.services.odoo.appraisal_service import get_appraisal_service
from app.services.ai.gemini_client import get_gemini_client
from app.core.exceptions import AppraisalNotFoundError, OdooModuleNotFoundError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/cycles", response_model=List[AppraisalCycle])
async def list_appraisal_cycles(
    state: Optional[str] = Query(None, description="Filter by state"),
):
    """List appraisal cycles."""
    service = get_appraisal_service()
    try:
        cycles = service.get_cycles(state=state)
        return cycles
    except OdooModuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message),
        )


@router.get("/cycles/{cycle_id}", response_model=AppraisalCycle)
async def get_appraisal_cycle(cycle_id: int):
    """Get appraisal cycle details."""
    service = get_appraisal_service()
    try:
        cycle = service.get_cycle_by_id(cycle_id)
        if not cycle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appraisal cycle {cycle_id} not found",
            )
        return cycle
    except OdooModuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message),
        )


@router.get("/cycles/{cycle_id}/status")
async def get_cycle_status(cycle_id: int):
    """Get completion status for an appraisal cycle."""
    service = get_appraisal_service()
    try:
        status_data = service.get_cycle_status(cycle_id)
        return status_data
    except OdooModuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message),
        )


@router.get("", response_model=PaginatedResponse)
async def list_appraisals(
    employee_id: Optional[int] = Query(None),
    manager_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    state: Optional[str] = Query(None, description="Filter by state: new, pending, done"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List appraisals with filters."""
    service = get_appraisal_service()
    try:
        filters = AppraisalFilter(
            employee_id=employee_id,
            manager_id=manager_id,
            department_id=department_id,
            state=state,
        )
        result = service.get_appraisals(filters, page=page, page_size=page_size)
        return result
    except OdooModuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message),
        )


@router.get("/pending", response_model=List[Appraisal])
async def list_pending_appraisals(
    manager_id: Optional[int] = Query(None, description="Filter by manager"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    days_until_deadline: int = Query(
        30, ge=1, description="Show appraisals due within this many days"
    ),
):
    """Get pending appraisals requiring action."""
    service = get_appraisal_service()
    try:
        appraisals = service.get_pending_appraisals(
            manager_id=manager_id,
            department_id=department_id,
            days_until_deadline=days_until_deadline,
        )
        return appraisals
    except OdooModuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message),
        )


@router.get("/{appraisal_id}", response_model=AppraisalDetail)
async def get_appraisal(appraisal_id: int):
    """Get appraisal details with goals and notes."""
    service = get_appraisal_service()
    try:
        appraisal = service.get_appraisal_by_id(appraisal_id)
        if not appraisal:
            raise AppraisalNotFoundError(f"Appraisal {appraisal_id} not found")
        return appraisal
    except AppraisalNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.message))
    except OdooModuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message),
        )


@router.get("/employee/{employee_id}", response_model=List[Appraisal])
async def get_employee_appraisals(employee_id: int):
    """Get all appraisals for an employee."""
    service = get_appraisal_service()
    try:
        appraisals = service.get_appraisals_by_employee(employee_id)
        return appraisals
    except OdooModuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message),
        )


@router.post("/{appraisal_id}/summarize", response_model=AppraisalSummary)
async def summarize_appraisal(appraisal_id: int):
    """AI-summarize appraisal feedback."""
    service = get_appraisal_service()
    gemini = get_gemini_client()

    if not gemini.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not available",
        )

    try:
        # Get appraisal with notes and goals
        appraisal = service.get_appraisal_by_id(appraisal_id)
        if not appraisal:
            raise AppraisalNotFoundError(f"Appraisal {appraisal_id} not found")

        # Format feedback notes
        notes_text = "\n".join(
            [f"- {note.get('author_name', 'Unknown')}: {note.get('note', '')}"
             for note in appraisal.get("notes", [])]
        )

        # Format goals
        goals_text = "\n".join(
            [f"- {goal.get('name', '')}: {goal.get('progression', 0)}% complete"
             for goal in appraisal.get("goals", [])]
        )

        # Summarize with AI
        summary = await gemini.summarize_appraisal(
            feedback_notes=notes_text or "No feedback notes available",
            goals=goals_text or "No goals defined",
        )

        # Store summary (if supported)
        service.update_appraisal_summary(appraisal_id, summary)

        return summary

    except AppraisalNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.message))


@router.get("/{appraisal_id}/insights")
async def get_appraisal_insights(appraisal_id: int):
    """Get AI insights for an appraisal (cached if available)."""
    service = get_appraisal_service()
    try:
        appraisal = service.get_appraisal_by_id(appraisal_id)
        if not appraisal:
            raise AppraisalNotFoundError(f"Appraisal {appraisal_id} not found")

        # Return cached summary if available
        if appraisal.get("ai_summary"):
            return appraisal["ai_summary"]

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No AI insights available. Run /summarize first.",
        )

    except AppraisalNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.message))


@router.post("/reminders/send")
async def send_reminders(request: SendRemindersRequest):
    """Manually trigger appraisal reminders."""
    service = get_appraisal_service()
    try:
        result = service.send_reminders(
            appraisal_ids=request.appraisal_ids,
            days_until_deadline=request.days_until_deadline,
        )
        return {
            "success": True,
            "reminders_sent": result.get("count", 0),
            "message": f"Sent {result.get('count', 0)} reminders",
        }
    except OdooModuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message),
        )


@router.get("/reminders/status", response_model=ReminderStatus)
async def get_reminder_status():
    """Check status of reminder job."""
    service = get_appraisal_service()
    try:
        status_data = service.get_reminder_status()
        return status_data
    except Exception as e:
        return ReminderStatus(
            status="unknown",
            reminders_sent=0,
        )
