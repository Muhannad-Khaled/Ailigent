"""Task management API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.exceptions import TaskNotFoundError
from app.core.security import verify_api_key
from app.models.task import (
    TaskAssignRequest,
    TaskListResponse,
    TaskResponse,
    TaskUpdate,
    OverdueTasksResponse,
    WorkloadResponse,
)
from app.services.odoo.client import OdooClient, get_odoo_client
from app.services.odoo.task_service import OdooTaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def get_task_service() -> OdooTaskService:
    """Get task service with Odoo client."""
    return OdooTaskService(get_odoo_client())


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    project_id: Optional[int] = None,
    include_closed: bool = False,
    service: OdooTaskService = Depends(get_task_service),
    _: str = Depends(verify_api_key),
):
    """
    List all tasks with optional filtering.

    - **limit**: Maximum number of tasks to return (1-500)
    - **offset**: Number of tasks to skip for pagination
    - **project_id**: Filter by specific project
    - **include_closed**: Include completed/closed tasks
    """
    tasks = service.get_all_tasks(
        limit=limit,
        offset=offset,
        project_id=project_id,
        include_closed=include_closed,
    )

    return TaskListResponse(
        tasks=[TaskResponse(**t) for t in tasks],
        total=len(tasks),
        page=(offset // limit) + 1 if limit > 0 else 1,
        page_size=limit,
    )


@router.get("/overdue", response_model=OverdueTasksResponse)
async def get_overdue_tasks(
    service: OdooTaskService = Depends(get_task_service),
    _: str = Depends(verify_api_key),
):
    """Get all tasks that are past their deadline and not completed."""
    tasks = service.get_overdue_tasks()

    return OverdueTasksResponse(
        tasks=[TaskResponse(**t) for t in tasks],
        count=len(tasks),
    )


@router.get("/stages")
async def get_stage_statistics(
    service: OdooTaskService = Depends(get_task_service),
    _: str = Depends(verify_api_key),
):
    """Get task count statistics by stage."""
    return service.get_stage_statistics()


@router.get("/completion-rates")
async def get_completion_rates(
    days: int = Query(30, ge=1, le=365),
    project_id: Optional[int] = None,
    service: OdooTaskService = Depends(get_task_service),
    _: str = Depends(verify_api_key),
):
    """
    Get task completion statistics.

    - **days**: Number of days to analyze (1-365)
    - **project_id**: Filter by specific project
    """
    from datetime import date, timedelta

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    return service.get_completion_rates(
        start_date=start_date,
        end_date=end_date,
        project_id=project_id,
    )


@router.get("/workload/{user_id}", response_model=WorkloadResponse)
async def get_employee_workload(
    user_id: int,
    service: OdooTaskService = Depends(get_task_service),
    _: str = Depends(verify_api_key),
):
    """
    Get workload metrics for a specific employee.

    - **user_id**: Odoo user ID
    """
    workload = service.get_employee_workload(user_id)
    return WorkloadResponse(**workload)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    service: OdooTaskService = Depends(get_task_service),
    _: str = Depends(verify_api_key),
):
    """Get a single task by ID."""
    try:
        task = service.get_task_by_id(task_id)
        return TaskResponse(**task)
    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{task_id}")
async def update_task(
    task_id: int,
    update: TaskUpdate,
    service: OdooTaskService = Depends(get_task_service),
    _: str = Depends(verify_api_key),
):
    """
    Update a task's fields.

    Only non-null fields in the request body will be updated.
    """
    try:
        values = update.model_dump(exclude_unset=True, exclude_none=True)
        if not values:
            raise HTTPException(
                status_code=400,
                detail="No fields to update",
            )

        # Convert user_ids to Odoo format if present
        if "user_ids" in values:
            values["user_ids"] = [(6, 0, values["user_ids"])]

        success = service.update_task(task_id, values)
        if success:
            return {"message": "Task updated successfully", "task_id": task_id}
        raise HTTPException(status_code=400, detail="Failed to update task")

    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{task_id}/assign")
async def assign_task(
    task_id: int,
    request: TaskAssignRequest,
    service: OdooTaskService = Depends(get_task_service),
    _: str = Depends(verify_api_key),
):
    """
    Assign a task to one or more employees.

    This replaces all current assignees with the specified users.
    """
    try:
        success = service.assign_task(task_id, request.user_ids)
        if success:
            return {
                "message": "Task assigned successfully",
                "task_id": task_id,
                "assigned_to": request.user_ids,
            }
        raise HTTPException(status_code=400, detail="Failed to assign task")

    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
