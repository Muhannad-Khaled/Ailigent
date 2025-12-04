"""AI-powered task distribution API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.exceptions import TaskNotFoundError
from app.core.security import verify_api_key
from app.models.task import TaskDistributionRecommendation, WorkloadBalanceAnalysis
from app.services.odoo.client import get_odoo_client
from app.services.odoo.task_service import OdooTaskService
from app.services.odoo.employee_service import OdooEmployeeService
from app.services.ai.gemini_client import get_gemini_client
from app.services.ai.workload_optimizer import WorkloadOptimizer
from app.services.ai.bottleneck_detector import BottleneckDetector

router = APIRouter(prefix="/distribution", tags=["AI Distribution"])


def get_task_service() -> OdooTaskService:
    return OdooTaskService(get_odoo_client())


def get_employee_service() -> OdooEmployeeService:
    return OdooEmployeeService(get_odoo_client())


def get_workload_optimizer() -> WorkloadOptimizer:
    return WorkloadOptimizer(get_gemini_client())


def get_bottleneck_detector() -> BottleneckDetector:
    return BottleneckDetector(get_gemini_client())


@router.post("/recommend/{task_id}", response_model=TaskDistributionRecommendation)
async def get_task_assignment_recommendation(
    task_id: int,
    department_id: Optional[int] = None,
    max_utilization: float = Query(80.0, ge=0, le=100),
    task_service: OdooTaskService = Depends(get_task_service),
    employee_service: OdooEmployeeService = Depends(get_employee_service),
    optimizer: WorkloadOptimizer = Depends(get_workload_optimizer),
    _: str = Depends(verify_api_key),
):
    """
    Get AI-powered recommendation for task assignment.

    Uses workload analysis and AI to recommend the best employee for a task.

    - **task_id**: Task to assign
    - **department_id**: Limit recommendations to a department
    - **max_utilization**: Maximum employee utilization to consider (0-100)
    """
    try:
        task = task_service.get_task_by_id(task_id)
    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Get available employees
    available = employee_service.get_available_assignees(
        max_utilization=max_utilization,
        department_id=department_id,
    )

    if not available:
        raise HTTPException(
            status_code=400,
            detail="No employees available for assignment within utilization threshold",
        )

    recommendation = await optimizer.recommend_task_assignment(
        task=task,
        available_employees=available,
    )

    return TaskDistributionRecommendation(
        task_id=task_id,
        task_name=task.get("name", ""),
        **recommendation,
    )


@router.post("/auto-assign/{task_id}")
async def auto_assign_task(
    task_id: int,
    department_id: Optional[int] = None,
    max_utilization: float = Query(80.0, ge=0, le=100),
    task_service: OdooTaskService = Depends(get_task_service),
    employee_service: OdooEmployeeService = Depends(get_employee_service),
    optimizer: WorkloadOptimizer = Depends(get_workload_optimizer),
    _: str = Depends(verify_api_key),
):
    """
    Automatically assign a task using AI recommendation.

    Gets AI recommendation and immediately assigns the task.

    - **task_id**: Task to assign
    - **department_id**: Limit to a department
    - **max_utilization**: Maximum utilization threshold
    """
    try:
        task = task_service.get_task_by_id(task_id)
    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    available = employee_service.get_available_assignees(
        max_utilization=max_utilization,
        department_id=department_id,
    )

    if not available:
        raise HTTPException(
            status_code=400,
            detail="No employees available for assignment",
        )

    recommendation = await optimizer.recommend_task_assignment(
        task=task,
        available_employees=available,
    )

    recommended_id = recommendation.get("recommended_employee_id")
    if not recommended_id:
        raise HTTPException(
            status_code=400,
            detail="Unable to determine best assignee",
        )

    # Assign the task
    success = task_service.assign_task(task_id, [recommended_id])

    if not success:
        raise HTTPException(status_code=500, detail="Failed to assign task")

    return {
        "message": "Task auto-assigned successfully",
        "task_id": task_id,
        "task_name": task.get("name"),
        "assigned_to_id": recommended_id,
        "assigned_to_name": recommendation.get("recommended_employee_name"),
        "confidence_score": recommendation.get("confidence_score"),
        "reasoning": recommendation.get("reasoning"),
    }


@router.get("/balance", response_model=WorkloadBalanceAnalysis)
async def get_workload_balance_analysis(
    department_id: Optional[int] = None,
    employee_service: OdooEmployeeService = Depends(get_employee_service),
    task_service: OdooTaskService = Depends(get_task_service),
    optimizer: WorkloadOptimizer = Depends(get_workload_optimizer),
    _: str = Depends(verify_api_key),
):
    """
    Get AI analysis of current workload distribution.

    Analyzes team workload and identifies imbalances.

    - **department_id**: Filter by department
    """
    # Get team workload
    workload = employee_service.get_team_workload_summary(department_id=department_id)
    employees = workload.get("employees", [])

    # Get pending tasks
    tasks = task_service.get_all_tasks(limit=500, include_closed=False)

    analysis = await optimizer.analyze_team_workload(
        employees=employees,
        tasks=tasks,
    )

    return WorkloadBalanceAnalysis(**analysis)


@router.get("/bottlenecks")
async def get_bottleneck_analysis(
    department_id: Optional[int] = None,
    employee_service: OdooEmployeeService = Depends(get_employee_service),
    task_service: OdooTaskService = Depends(get_task_service),
    detector: BottleneckDetector = Depends(get_bottleneck_detector),
    _: str = Depends(verify_api_key),
):
    """
    Get AI analysis of workflow bottlenecks.

    Identifies stage bottlenecks, employee bottlenecks, and process issues.

    - **department_id**: Filter employees by department
    """
    # Get all data needed for analysis
    tasks = task_service.get_all_tasks(limit=1000, include_closed=False)
    stages = task_service.get_stage_statistics()
    workload = employee_service.get_team_workload_summary(department_id=department_id)

    analysis = await detector.detect_bottlenecks(
        tasks=tasks,
        employees=workload.get("employees", []),
        stages=stages,
    )

    return analysis


@router.post("/rebalance-suggestions")
async def get_rebalancing_suggestions(
    department_id: Optional[int] = None,
    employee_service: OdooEmployeeService = Depends(get_employee_service),
    optimizer: WorkloadOptimizer = Depends(get_workload_optimizer),
    _: str = Depends(verify_api_key),
):
    """
    Get suggestions for rebalancing workload across the team.

    Identifies overloaded and underutilized employees and suggests transfers.

    - **department_id**: Filter by department
    """
    workload = employee_service.get_team_workload_summary(department_id=department_id)

    suggestions = await optimizer.suggest_rebalancing(workload)

    return suggestions
