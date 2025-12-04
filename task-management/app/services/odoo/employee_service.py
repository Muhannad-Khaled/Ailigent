"""Employee Service - Operations on hr.employee and res.users models in Odoo."""

import logging
from typing import Any, Dict, List, Optional

from app.core.constants import (
    DEFAULT_EMPLOYEE_FIELDS,
    DEFAULT_WEEKLY_HOURS,
    ODOO_MODEL_EMPLOYEE,
    ODOO_MODEL_USER,
    ODOO_MODEL_DEPARTMENT,
    WORKLOAD_OVERLOADED_THRESHOLD,
    WORKLOAD_UNDERUTILIZED_THRESHOLD,
)
from app.core.exceptions import EmployeeNotFoundError
from app.services.odoo.client import OdooClient
from app.services.odoo.task_service import OdooTaskService

logger = logging.getLogger(__name__)


class OdooEmployeeService:
    """Service for managing employees via Odoo API."""

    def __init__(self, client: OdooClient):
        self.client = client
        self.task_service = OdooTaskService(client)

    def get_all_employees(
        self,
        limit: int = 100,
        offset: int = 0,
        department_id: Optional[int] = None,
        active_only: bool = True,
    ) -> List[Dict]:
        """
        Fetch all employees with pagination.

        Args:
            limit: Maximum employees to return
            offset: Number to skip
            department_id: Filter by department
            active_only: Only active employees

        Returns:
            List of employee dictionaries
        """
        domain = []

        if active_only:
            domain.append(("active", "=", True))

        if department_id:
            domain.append(("department_id", "=", department_id))

        return self.client.search_read(
            ODOO_MODEL_EMPLOYEE,
            domain,
            fields=DEFAULT_EMPLOYEE_FIELDS,
            limit=limit,
            offset=offset,
            order="name asc",
        )

    def get_employee_by_id(self, employee_id: int) -> Dict:
        """
        Get a single employee by ID.

        Args:
            employee_id: Employee ID

        Returns:
            Employee dictionary

        Raises:
            EmployeeNotFoundError: If employee not found
        """
        employees = self.client.read(
            ODOO_MODEL_EMPLOYEE,
            [employee_id],
            DEFAULT_EMPLOYEE_FIELDS,
        )

        if not employees:
            raise EmployeeNotFoundError(
                f"Employee {employee_id} not found",
                details={"employee_id": employee_id},
            )

        return employees[0]

    def get_employee_by_user_id(self, user_id: int) -> Optional[Dict]:
        """
        Get employee by linked user ID.

        Args:
            user_id: Odoo user ID

        Returns:
            Employee dictionary or None
        """
        employees = self.client.search_read(
            ODOO_MODEL_EMPLOYEE,
            [("user_id", "=", user_id)],
            fields=DEFAULT_EMPLOYEE_FIELDS,
            limit=1,
        )

        return employees[0] if employees else None

    def get_user_by_id(self, user_id: int) -> Dict:
        """
        Get user details by ID.

        Args:
            user_id: User ID

        Returns:
            User dictionary
        """
        users = self.client.read(
            ODOO_MODEL_USER,
            [user_id],
            ["id", "name", "login", "email", "active"],
        )

        if not users:
            raise EmployeeNotFoundError(
                f"User {user_id} not found",
                details={"user_id": user_id},
            )

        return users[0]

    def get_all_users_with_tasks(self) -> List[Dict]:
        """
        Get all users who have tasks assigned.

        Returns:
            List of user dictionaries with basic task info
        """
        # Get users who have at least one task
        users = self.client.search_read(
            ODOO_MODEL_USER,
            [("active", "=", True)],
            fields=["id", "name", "email"],
        )

        result = []
        for user in users:
            # Note: In Odoo 18, we can't use dotted fields like 'stage_id.is_closed' in domain
            task_count = self.client.search_count(
                "project.task",
                [
                    ("user_ids", "in", [user["id"]]),
                ],
            )
            if task_count > 0:
                user["active_task_count"] = task_count
                result.append(user)

        return result

    def get_employee_workload_details(
        self,
        employee_id: int,
        weekly_capacity: float = DEFAULT_WEEKLY_HOURS,
    ) -> Dict[str, Any]:
        """
        Get detailed workload information for an employee.

        Args:
            employee_id: Employee ID
            weekly_capacity: Weekly working hours capacity

        Returns:
            Detailed workload information
        """
        employee = self.get_employee_by_id(employee_id)
        user_id = employee.get("user_id")

        if not user_id:
            return {
                "employee_id": employee_id,
                "employee_name": employee["name"],
                "error": "Employee has no linked user account",
            }

        # Get user_id from tuple if needed
        if isinstance(user_id, (list, tuple)):
            user_id = user_id[0]

        workload = self.task_service.get_employee_workload(user_id)

        utilization = (
            workload["total_remaining_hours"] / weekly_capacity * 100
            if weekly_capacity > 0
            else 0
        )

        return {
            "employee_id": employee_id,
            "employee_name": employee["name"],
            "user_id": user_id,
            "email": employee.get("work_email"),
            "department": employee.get("department_id", [None, "N/A"])[1]
            if employee.get("department_id")
            else "N/A",
            "job_title": employee.get("job_title"),
            "total_tasks": workload["total_tasks"],
            "total_planned_hours": workload["total_planned_hours"],
            "total_remaining_hours": workload["total_remaining_hours"],
            "high_priority_count": workload["high_priority_count"],
            "blocked_count": workload["blocked_count"],
            "overdue_count": workload["overdue_count"],
            "weekly_capacity": weekly_capacity,
            "utilization_percentage": round(utilization, 2),
            "status": self._get_workload_status(utilization),
            "tasks": workload["tasks"],
        }

    def _get_workload_status(self, utilization: float) -> str:
        """Determine workload status based on utilization percentage."""
        if utilization >= WORKLOAD_OVERLOADED_THRESHOLD * 100:
            return "overloaded"
        elif utilization <= WORKLOAD_UNDERUTILIZED_THRESHOLD * 100:
            return "underutilized"
        return "balanced"

    def get_team_workload_summary(
        self,
        department_id: Optional[int] = None,
        weekly_capacity: float = DEFAULT_WEEKLY_HOURS,
    ) -> Dict[str, Any]:
        """
        Get workload summary for team/department.

        Args:
            department_id: Optional department filter
            weekly_capacity: Weekly capacity per employee

        Returns:
            Team workload summary
        """
        employees = self.get_all_employees(
            department_id=department_id,
            limit=500,
        )

        workloads = []
        total_tasks = 0
        total_hours = 0
        overloaded_count = 0
        underutilized_count = 0

        for emp in employees:
            user_id = emp.get("user_id")
            if not user_id:
                continue

            if isinstance(user_id, (list, tuple)):
                user_id = user_id[0]

            try:
                workload = self.task_service.get_employee_workload(user_id)
                utilization = (
                    workload["total_remaining_hours"] / weekly_capacity * 100
                    if weekly_capacity > 0
                    else 0
                )

                status = self._get_workload_status(utilization)
                if status == "overloaded":
                    overloaded_count += 1
                elif status == "underutilized":
                    underutilized_count += 1

                total_tasks += workload["total_tasks"]
                total_hours += workload["total_remaining_hours"]

                workloads.append({
                    "employee_id": emp["id"],
                    "employee_name": emp["name"],
                    "user_id": user_id,
                    "task_count": workload["total_tasks"],
                    "remaining_hours": workload["total_remaining_hours"],
                    "utilization": round(utilization, 2),
                    "status": status,
                    "high_priority": workload["high_priority_count"],
                    "overdue": workload["overdue_count"],
                })

            except Exception as e:
                logger.warning(f"Error getting workload for employee {emp['id']}: {e}")

        avg_utilization = (
            sum(w["utilization"] for w in workloads) / len(workloads)
            if workloads
            else 0
        )

        return {
            "total_employees": len(workloads),
            "total_tasks": total_tasks,
            "total_remaining_hours": total_hours,
            "average_utilization": round(avg_utilization, 2),
            "overloaded_count": overloaded_count,
            "underutilized_count": underutilized_count,
            "balanced_count": len(workloads) - overloaded_count - underutilized_count,
            "employees": sorted(
                workloads,
                key=lambda x: x["utilization"],
                reverse=True,
            ),
        }

    def get_departments(self) -> List[Dict]:
        """
        Get all departments.

        Returns:
            List of department dictionaries
        """
        return self.client.search_read(
            ODOO_MODEL_DEPARTMENT,
            [],
            fields=["id", "name", "manager_id", "parent_id"],
            order="name asc",
        )

    def get_available_assignees(
        self,
        max_utilization: float = WORKLOAD_OVERLOADED_THRESHOLD * 100,
        department_id: Optional[int] = None,
    ) -> List[Dict]:
        """
        Get employees available for task assignment.

        Args:
            max_utilization: Maximum utilization percentage to consider available
            department_id: Optional department filter

        Returns:
            List of available employees with workload info
        """
        summary = self.get_team_workload_summary(department_id=department_id)

        available = [
            emp
            for emp in summary["employees"]
            if emp["utilization"] < max_utilization
        ]

        return sorted(available, key=lambda x: x["utilization"])
