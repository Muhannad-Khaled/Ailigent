"""Employee management API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.exceptions import EmployeeNotFoundError
from app.core.security import verify_api_key
from app.models.employee import (
    EmployeeResponse,
    EmployeeWorkload,
    TeamWorkloadSummary,
)
from app.services.odoo.client import get_odoo_client
from app.services.odoo.employee_service import OdooEmployeeService

router = APIRouter(prefix="/employees", tags=["Employees"])


def get_employee_service() -> OdooEmployeeService:
    """Get employee service with Odoo client."""
    return OdooEmployeeService(get_odoo_client())


@router.get("")
async def list_employees(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    department_id: Optional[int] = None,
    active_only: bool = True,
    service: OdooEmployeeService = Depends(get_employee_service),
    _: str = Depends(verify_api_key),
):
    """
    List all employees with optional filtering.

    - **limit**: Maximum employees to return (1-500)
    - **offset**: Number to skip for pagination
    - **department_id**: Filter by department
    - **active_only**: Only return active employees
    """
    employees = service.get_all_employees(
        limit=limit,
        offset=offset,
        department_id=department_id,
        active_only=active_only,
    )

    return {
        "employees": [EmployeeResponse(**e) for e in employees],
        "total": len(employees),
    }


@router.get("/departments")
async def list_departments(
    service: OdooEmployeeService = Depends(get_employee_service),
    _: str = Depends(verify_api_key),
):
    """Get all departments."""
    departments = service.get_departments()
    return {"departments": departments}


@router.get("/with-tasks")
async def list_employees_with_tasks(
    service: OdooEmployeeService = Depends(get_employee_service),
    _: str = Depends(verify_api_key),
):
    """Get all users who have active tasks assigned."""
    users = service.get_all_users_with_tasks()
    return {"users": users, "total": len(users)}


@router.get("/available")
async def get_available_assignees(
    max_utilization: float = Query(80.0, ge=0, le=100),
    department_id: Optional[int] = None,
    service: OdooEmployeeService = Depends(get_employee_service),
    _: str = Depends(verify_api_key),
):
    """
    Get employees available for task assignment.

    Returns employees whose current utilization is below the threshold.

    - **max_utilization**: Maximum utilization percentage (0-100)
    - **department_id**: Filter by department
    """
    available = service.get_available_assignees(
        max_utilization=max_utilization,
        department_id=department_id,
    )

    return {
        "available_employees": available,
        "total": len(available),
        "max_utilization_threshold": max_utilization,
    }


@router.get("/workload-summary", response_model=TeamWorkloadSummary)
async def get_team_workload_summary(
    department_id: Optional[int] = None,
    weekly_capacity: float = Query(40.0, ge=1, le=80),
    service: OdooEmployeeService = Depends(get_employee_service),
    _: str = Depends(verify_api_key),
):
    """
    Get workload summary for all employees.

    - **department_id**: Filter by department
    - **weekly_capacity**: Weekly working hours per employee
    """
    summary = service.get_team_workload_summary(
        department_id=department_id,
        weekly_capacity=weekly_capacity,
    )

    return TeamWorkloadSummary(**summary)


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: int,
    service: OdooEmployeeService = Depends(get_employee_service),
    _: str = Depends(verify_api_key),
):
    """Get a single employee by ID."""
    try:
        employee = service.get_employee_by_id(employee_id)
        return EmployeeResponse(**employee)
    except EmployeeNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{employee_id}/workload", response_model=EmployeeWorkload)
async def get_employee_workload(
    employee_id: int,
    weekly_capacity: float = Query(40.0, ge=1, le=80),
    service: OdooEmployeeService = Depends(get_employee_service),
    _: str = Depends(verify_api_key),
):
    """
    Get detailed workload information for an employee.

    - **employee_id**: Employee ID
    - **weekly_capacity**: Weekly working hours capacity
    """
    try:
        workload = service.get_employee_workload_details(
            employee_id=employee_id,
            weekly_capacity=weekly_capacity,
        )

        if "error" in workload:
            raise HTTPException(status_code=400, detail=workload["error"])

        return EmployeeWorkload(**workload)

    except EmployeeNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
