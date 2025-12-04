"""Report generation API endpoints."""

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.security import verify_api_key
from app.models.report import (
    ProductivityMetrics,
    ReportRequest,
    BottleneckAnalysisResponse,
)
from app.services.odoo.client import get_odoo_client
from app.services.odoo.task_service import OdooTaskService
from app.services.odoo.employee_service import OdooEmployeeService

router = APIRouter(prefix="/reports", tags=["Reports"])


def get_task_service() -> OdooTaskService:
    """Get task service with Odoo client."""
    return OdooTaskService(get_odoo_client())


def get_employee_service() -> OdooEmployeeService:
    """Get employee service with Odoo client."""
    return OdooEmployeeService(get_odoo_client())


@router.get("/productivity", response_model=ProductivityMetrics)
async def get_productivity_metrics(
    days: int = Query(30, ge=1, le=365),
    project_id: Optional[int] = None,
    task_service: OdooTaskService = Depends(get_task_service),
    _: str = Depends(verify_api_key),
):
    """
    Get productivity metrics for a period.

    - **days**: Number of days to analyze (1-365)
    - **project_id**: Filter by specific project
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    completion_data = task_service.get_completion_rates(
        start_date=start_date,
        end_date=end_date,
        project_id=project_id,
    )

    return ProductivityMetrics(**completion_data)


@router.get("/stages")
async def get_stage_report(
    task_service: OdooTaskService = Depends(get_task_service),
    _: str = Depends(verify_api_key),
):
    """Get detailed report on task distribution across stages."""
    stage_stats = task_service.get_stage_statistics()

    total_tasks = sum(s["task_count"] for s in stage_stats)
    closed_tasks = sum(s["task_count"] for s in stage_stats if s.get("is_closed"))

    return {
        "stages": stage_stats,
        "summary": {
            "total_tasks": total_tasks,
            "completed_tasks": closed_tasks,
            "in_progress_tasks": total_tasks - closed_tasks,
            "completion_percentage": round(
                (closed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 2
            ),
        },
    }


@router.get("/workload")
async def get_workload_report(
    department_id: Optional[int] = None,
    weekly_capacity: float = Query(40.0, ge=1, le=80),
    employee_service: OdooEmployeeService = Depends(get_employee_service),
    _: str = Depends(verify_api_key),
):
    """
    Get team workload distribution report.

    - **department_id**: Filter by department
    - **weekly_capacity**: Weekly working hours per employee
    """
    summary = employee_service.get_team_workload_summary(
        department_id=department_id,
        weekly_capacity=weekly_capacity,
    )

    # Add distribution analysis
    distribution = {
        "overloaded_percentage": round(
            (summary["overloaded_count"] / summary["total_employees"] * 100)
            if summary["total_employees"] > 0
            else 0,
            2,
        ),
        "underutilized_percentage": round(
            (summary["underutilized_count"] / summary["total_employees"] * 100)
            if summary["total_employees"] > 0
            else 0,
            2,
        ),
        "balanced_percentage": round(
            (summary["balanced_count"] / summary["total_employees"] * 100)
            if summary["total_employees"] > 0
            else 0,
            2,
        ),
    }

    return {
        **summary,
        "distribution": distribution,
        "recommendations": _generate_workload_recommendations(summary),
    }


def _generate_workload_recommendations(summary: dict) -> list:
    """Generate basic workload recommendations."""
    recommendations = []

    if summary["overloaded_count"] > 0:
        recommendations.append(
            f"{summary['overloaded_count']} employee(s) are overloaded. "
            "Consider redistributing tasks or extending deadlines."
        )

    if summary["underutilized_count"] > 0:
        recommendations.append(
            f"{summary['underutilized_count']} employee(s) have capacity available. "
            "Consider assigning them tasks from overloaded colleagues."
        )

    if summary["average_utilization"] > 80:
        recommendations.append(
            "Team average utilization is high (>80%). "
            "Monitor for burnout and consider hiring or deprioritizing tasks."
        )
    elif summary["average_utilization"] < 40:
        recommendations.append(
            "Team average utilization is low (<40%). "
            "Review project pipeline and task allocation."
        )

    if not recommendations:
        recommendations.append("Workload distribution appears balanced.")

    return recommendations


@router.get("/overdue-summary")
async def get_overdue_summary(
    task_service: OdooTaskService = Depends(get_task_service),
    _: str = Depends(verify_api_key),
):
    """Get summary of overdue tasks with severity breakdown."""
    from datetime import datetime

    overdue_tasks = task_service.get_overdue_tasks()

    if not overdue_tasks:
        return {
            "total_overdue": 0,
            "by_severity": {},
            "by_project": {},
            "tasks": [],
        }

    today = date.today()
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    by_project = {}

    for task in overdue_tasks:
        # Calculate days overdue
        deadline = task.get("date_deadline")
        if deadline:
            deadline_date = datetime.fromisoformat(deadline).date()
            days_overdue = (today - deadline_date).days

            # Categorize by severity
            if days_overdue > 7:
                severity_counts["critical"] += 1
            elif days_overdue > 3:
                severity_counts["high"] += 1
            elif days_overdue > 1:
                severity_counts["medium"] += 1
            else:
                severity_counts["low"] += 1

            task["days_overdue"] = days_overdue

        # Group by project
        project = task.get("project_id")
        if project and isinstance(project, list) and len(project) > 1:
            project_name = project[1]
            by_project[project_name] = by_project.get(project_name, 0) + 1

    return {
        "total_overdue": len(overdue_tasks),
        "by_severity": severity_counts,
        "by_project": by_project,
        "tasks": overdue_tasks[:20],  # Return first 20 for preview
    }


@router.post("/generate")
async def generate_custom_report(
    request: ReportRequest,
    task_service: OdooTaskService = Depends(get_task_service),
    employee_service: OdooEmployeeService = Depends(get_employee_service),
    _: str = Depends(verify_api_key),
):
    """
    Generate a custom report based on specified parameters.

    Combines productivity metrics, workload analysis, and stage distribution.
    """
    # Determine date range
    end_date = request.end_date or date.today()
    if request.start_date:
        start_date = request.start_date
    else:
        days_map = {"daily": 1, "weekly": 7, "monthly": 30}
        days = days_map.get(request.report_type, 30)
        start_date = end_date - timedelta(days=days)

    # Get completion rates
    completion = task_service.get_completion_rates(
        start_date=start_date,
        end_date=end_date,
        project_id=request.project_ids[0] if request.project_ids else None,
    )

    # Get stage statistics
    stages = task_service.get_stage_statistics()

    # Get workload summary
    workload = employee_service.get_team_workload_summary(
        department_id=request.department_id
    )

    # Get overdue tasks
    overdue = task_service.get_overdue_tasks()

    return {
        "report_type": request.report_type,
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "productivity": completion,
        "stage_distribution": stages,
        "workload_summary": {
            "total_employees": workload["total_employees"],
            "average_utilization": workload["average_utilization"],
            "overloaded": workload["overloaded_count"],
            "underutilized": workload["underutilized_count"],
        },
        "overdue_count": len(overdue),
        "recommendations": _generate_workload_recommendations(workload),
    }
