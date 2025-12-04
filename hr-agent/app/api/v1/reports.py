"""HR Reports API Endpoints."""

import logging
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.models.report import (
    DepartmentReport,
    ExportRequest,
    GenerateReportRequest,
    HeadcountReport,
    ReportInsights,
    ReportMetadata,
    TurnoverReport,
)
from app.services.odoo.employee_service import get_employee_service
from app.services.ai.gemini_client import get_gemini_client

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/headcount", response_model=HeadcountReport)
async def get_headcount_report(
    as_of_date: Optional[date] = Query(None, description="Report date (default: today)"),
):
    """Get headcount report."""
    service = get_employee_service()
    try:
        report = service.get_headcount_report(as_of_date=as_of_date)
        return report
    except Exception as e:
        logger.error(f"Failed to generate headcount report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}",
        )


@router.get("/headcount/by-department")
async def get_headcount_by_department(
    as_of_date: Optional[date] = Query(None, description="Report date (default: today)"),
):
    """Get headcount breakdown by department."""
    service = get_employee_service()
    try:
        data = service.get_headcount_by_department(as_of_date=as_of_date)
        return {
            "date": as_of_date or date.today(),
            "departments": data,
        }
    except Exception as e:
        logger.error(f"Failed to get department headcount: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data: {str(e)}",
        )


@router.get("/turnover", response_model=TurnoverReport)
async def get_turnover_report(
    period_start: Optional[date] = Query(None, description="Period start date"),
    period_end: Optional[date] = Query(None, description="Period end date"),
):
    """Get turnover analytics report."""
    service = get_employee_service()
    try:
        report = service.get_turnover_report(
            period_start=period_start,
            period_end=period_end,
        )
        return report
    except Exception as e:
        logger.error(f"Failed to generate turnover report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}",
        )


@router.get("/turnover/trends")
async def get_turnover_trends(
    months: int = Query(12, ge=1, le=36, description="Number of months to analyze"),
):
    """Get turnover trends over time."""
    service = get_employee_service()
    try:
        trends = service.get_turnover_trends(months=months)
        return {
            "months_analyzed": months,
            "trends": trends,
        }
    except Exception as e:
        logger.error(f"Failed to get turnover trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data: {str(e)}",
        )


@router.get("/department/{department_id}", response_model=DepartmentReport)
async def get_department_report(department_id: int):
    """Get detailed metrics for a specific department."""
    service = get_employee_service()
    try:
        report = service.get_department_report(department_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department {department_id} not found",
            )
        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get department report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}",
        )


@router.post("/insights", response_model=ReportInsights)
async def generate_insights(
    include_headcount: bool = Query(True, description="Include headcount metrics"),
    include_turnover: bool = Query(True, description="Include turnover metrics"),
    include_attendance: bool = Query(False, description="Include attendance metrics"),
    period_months: int = Query(3, ge=1, le=12, description="Analysis period in months"),
):
    """Generate AI-powered HR insights."""
    service = get_employee_service()
    gemini = get_gemini_client()

    if not gemini.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not available",
        )

    try:
        # Gather metrics
        metrics = {}

        if include_headcount:
            metrics["headcount"] = service.get_headcount_report()

        if include_turnover:
            metrics["turnover"] = service.get_turnover_report()

        if include_attendance:
            from app.services.odoo.attendance_service import get_attendance_service
            attendance_service = get_attendance_service()
            metrics["attendance"] = attendance_service.get_summary()

        # Generate AI insights
        insights = await gemini.generate_hr_insights(metrics)

        return insights

    except Exception as e:
        logger.error(f"Failed to generate insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate insights: {str(e)}",
        )


@router.post("/generate", response_model=ReportMetadata)
async def generate_report(request: GenerateReportRequest):
    """Generate a custom report."""
    service = get_employee_service()
    try:
        metadata = service.generate_custom_report(
            report_type=request.report_type,
            date_from=request.date_from,
            date_to=request.date_to,
            department_ids=request.department_ids,
            include_ai_insights=request.include_ai_insights,
        )
        return metadata
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{report_id}")
async def get_report(report_id: str):
    """Get a previously generated report."""
    service = get_employee_service()
    try:
        report = service.get_report_by_id(report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found",
            )
        return report
    except HTTPException:
        raise


@router.get("/{report_id}/export/pdf")
async def export_report_pdf(report_id: str):
    """Export report as PDF."""
    service = get_employee_service()
    try:
        pdf_content = service.export_report_to_pdf(report_id)
        if not pdf_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found",
            )

        return StreamingResponse(
            iter([pdf_content]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=hr_report_{report_id}.pdf"
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export: {str(e)}",
        )


@router.get("/{report_id}/export/excel")
async def export_report_excel(report_id: str):
    """Export report as Excel."""
    service = get_employee_service()
    try:
        excel_content = service.export_report_to_excel(report_id)
        if not excel_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found",
            )

        return StreamingResponse(
            iter([excel_content]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=hr_report_{report_id}.xlsx"
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export Excel: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export: {str(e)}",
        )


@router.get("/list", response_model=List[ReportMetadata])
async def list_reports(
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    limit: int = Query(20, ge=1, le=100, description="Max reports to return"),
):
    """List previously generated reports."""
    service = get_employee_service()
    try:
        reports = service.list_reports(report_type=report_type, limit=limit)
        return reports
    except Exception as e:
        logger.error(f"Failed to list reports: {e}")
        return []
