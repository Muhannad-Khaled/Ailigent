"""Attendance Admin API Endpoints."""

import logging
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.models.attendance import (
    AttendanceAnomalyReport,
    AttendanceSummary,
    DepartmentAttendance,
    LeaveApprovalRequest,
    LeaveBalanceReport,
    LeaveRequest,
    LeaveRequestCreate,
    MonthlyAttendanceReport,
)
from app.models.common import PaginatedResponse
from app.services.odoo.attendance_service import get_attendance_service
from app.services.ai.gemini_client import get_gemini_client
from app.core.exceptions import LeaveRequestNotFoundError, OdooModuleNotFoundError

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================
# Leave Management
# ==================


@router.get("/leave/pending", response_model=List[LeaveRequest])
async def list_pending_leave_requests(
    department_id: Optional[int] = Query(None, description="Filter by department"),
    limit: int = Query(50, ge=1, le=100, description="Max requests to return"),
):
    """Get pending leave requests awaiting approval."""
    service = get_attendance_service()
    try:
        requests = service.get_pending_leave_requests(
            department_id=department_id,
            limit=limit,
        )
        return requests
    except OdooModuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message),
        )


@router.post("/leave/request", response_model=LeaveRequest)
async def create_leave_request(request: LeaveRequestCreate):
    """
    Create a new leave request (for demo purposes).

    This creates a leave request in "pending" state awaiting approval.

    Common leave_type_id values:
    - 1: Annual Leave
    - 2: Sick Leave
    - 4: Unpaid Leave

    Use GET /api/v1/attendance/leave/types to see available leave types.
    """
    service = get_attendance_service()
    try:
        result = service.create_leave_request(
            employee_id=request.employee_id,
            leave_type_id=request.leave_type_id,
            date_from=request.date_from,
            date_to=request.date_to,
            notes=request.notes,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except OdooModuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message),
        )
    except Exception as e:
        logger.error(f"Failed to create leave request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create leave request: {str(e)}",
        )


@router.post("/leave/{leave_id}/approve")
async def approve_leave_request(leave_id: int, request: LeaveApprovalRequest):
    """Approve a leave request."""
    service = get_attendance_service()
    try:
        result = service.approve_leave(leave_id, notes=request.notes)
        return {
            "success": True,
            "message": "Leave request approved",
            "leave_id": leave_id,
        }
    except LeaveRequestNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.message))
    except OdooModuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message),
        )
    except Exception as e:
        logger.error(f"Failed to approve leave: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve leave: {str(e)}",
        )


@router.post("/leave/{leave_id}/reject")
async def reject_leave_request(leave_id: int, request: LeaveApprovalRequest):
    """Reject a leave request."""
    service = get_attendance_service()
    try:
        result = service.reject_leave(leave_id, notes=request.notes)
        return {
            "success": True,
            "message": "Leave request rejected",
            "leave_id": leave_id,
        }
    except LeaveRequestNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.message))
    except OdooModuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message),
        )


@router.get("/leave/balance/report", response_model=List[LeaveBalanceReport])
async def get_leave_balance_report(
    department_id: Optional[int] = Query(None, description="Filter by department"),
):
    """Get department leave balances report."""
    service = get_attendance_service()
    try:
        report = service.get_leave_balance_report(department_id=department_id)
        return report
    except OdooModuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message),
        )


# ==================
# Attendance Analytics
# ==================


@router.get("/summary", response_model=AttendanceSummary)
async def get_attendance_summary(
    for_date: Optional[date] = Query(None, description="Date for summary (default: today)"),
):
    """Get organization-wide attendance summary."""
    service = get_attendance_service()
    try:
        summary = service.get_summary(for_date=for_date)
        return summary
    except OdooModuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message),
        )


@router.get("/department/{department_id}", response_model=DepartmentAttendance)
async def get_department_attendance(
    department_id: int,
    for_date: Optional[date] = Query(None, description="Date for attendance (default: today)"),
):
    """Get department attendance summary."""
    service = get_attendance_service()
    try:
        attendance = service.get_department_attendance(
            department_id=department_id,
            for_date=for_date,
        )
        if not attendance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department {department_id} not found",
            )
        return attendance
    except HTTPException:
        raise
    except OdooModuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message),
        )


@router.get("/anomalies", response_model=AttendanceAnomalyReport)
async def get_attendance_anomalies(
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
):
    """Get detected attendance anomalies."""
    service = get_attendance_service()
    gemini = get_gemini_client()

    try:
        # Get attendance data
        attendance_data = service.get_attendance_for_analysis(
            days=days,
            department_id=department_id,
        )

        # If AI is available, use it for analysis
        if gemini.is_available():
            analysis = await gemini.detect_attendance_anomalies(attendance_data)
            return AttendanceAnomalyReport(
                analysis_date=date.today(),
                period_start=attendance_data.get("period_start", date.today()),
                period_end=attendance_data.get("period_end", date.today()),
                anomalies=analysis.get("anomalies", []),
                summary=analysis.get("summary", {}),
                department_patterns=analysis.get("department_patterns", []),
                recommendations=analysis.get("recommendations", []),
                overall_assessment=analysis.get("overall_assessment", "Analysis unavailable"),
            )
        else:
            # Basic rule-based analysis
            anomalies = service.detect_anomalies_basic(attendance_data)
            return anomalies

    except OdooModuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message),
        )


@router.get("/anomalies/analyze")
async def analyze_attendance_patterns(
    days: int = Query(30, ge=7, le=90, description="Number of days to analyze"),
):
    """AI-powered deep analysis of attendance patterns."""
    service = get_attendance_service()
    gemini = get_gemini_client()

    if not gemini.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not available",
        )

    try:
        attendance_data = service.get_attendance_for_analysis(days=days)
        analysis = await gemini.detect_attendance_anomalies(attendance_data)
        return analysis
    except OdooModuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message),
        )


# ==================
# Attendance Reports
# ==================


@router.get("/reports/monthly", response_model=MonthlyAttendanceReport)
async def get_monthly_attendance_report(
    year: int = Query(..., ge=2020, le=2100, description="Year"),
    month: int = Query(..., ge=1, le=12, description="Month"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
):
    """Get monthly attendance report."""
    service = get_attendance_service()
    try:
        report = service.get_monthly_report(
            year=year,
            month=month,
            department_id=department_id,
        )
        return report
    except OdooModuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message),
        )


@router.get("/reports/department")
async def get_department_attendance_report(
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
):
    """Get department-wise attendance report."""
    service = get_attendance_service()
    try:
        report = service.get_department_report(
            date_from=date_from,
            date_to=date_to,
        )
        return report
    except OdooModuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message),
        )
