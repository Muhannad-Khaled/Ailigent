"""Task Service - Operations on project.task model in Odoo."""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core.constants import (
    DEFAULT_TASK_FIELDS,
    ODOO_MODEL_TASK,
    ODOO_MODEL_STAGE,
)
from app.core.exceptions import TaskNotFoundError
from app.services.odoo.client import OdooClient

logger = logging.getLogger(__name__)


class OdooTaskService:
    """Service for managing tasks via Odoo API."""

    def __init__(self, client: OdooClient):
        self.client = client
        self.model = ODOO_MODEL_TASK

    def get_all_tasks(
        self,
        limit: int = 100,
        offset: int = 0,
        project_id: Optional[int] = None,
        include_closed: bool = False,
    ) -> List[Dict]:
        """
        Fetch all tasks with pagination.

        Args:
            limit: Maximum tasks to return
            offset: Number of tasks to skip
            project_id: Filter by project ID
            include_closed: Include completed tasks

        Returns:
            List of task dictionaries
        """
        domain = []

        if project_id:
            domain.append(("project_id", "=", project_id))

        # Note: In Odoo 18, we can't use dotted fields like 'stage_id.is_closed' in domain
        # Fetch all tasks and filter in code, or use state field if available

        return self.client.search_read(
            self.model,
            domain,
            fields=DEFAULT_TASK_FIELDS,
            limit=limit,
            offset=offset,
            order="date_deadline asc, priority desc",
        )

    def get_task_by_id(self, task_id: int) -> Dict:
        """
        Get a single task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task dictionary

        Raises:
            TaskNotFoundError: If task not found
        """
        tasks = self.client.read(self.model, [task_id], DEFAULT_TASK_FIELDS)

        if not tasks:
            raise TaskNotFoundError(
                f"Task {task_id} not found",
                details={"task_id": task_id},
            )

        return tasks[0]

    def get_overdue_tasks(self) -> List[Dict]:
        """
        Get tasks past their deadline that are not completed.

        Returns:
            List of overdue tasks
        """
        today = date.today().isoformat()
        domain = [
            ("date_deadline", "<", today),
            ("date_deadline", "!=", False),
        ]

        tasks = self.client.search_read(
            self.model,
            domain,
            fields=DEFAULT_TASK_FIELDS,
            order="date_deadline asc",
        )

        logger.info(f"Found {len(tasks)} overdue tasks")
        return tasks

    def get_tasks_by_employee(
        self,
        user_ids: List[int],
        include_closed: bool = False,
    ) -> List[Dict]:
        """
        Get tasks assigned to specific users.

        Args:
            user_ids: List of user IDs
            include_closed: Include completed tasks

        Returns:
            List of tasks
        """
        domain = [("user_ids", "in", user_ids)]

        # Note: In Odoo 18, we can't use dotted fields like 'stage_id.is_closed' in domain

        return self.client.search_read(
            self.model,
            domain,
            fields=DEFAULT_TASK_FIELDS,
            order="date_deadline asc",
        )

    def get_employee_workload(self, user_id: int) -> Dict[str, Any]:
        """
        Calculate workload for a specific employee.

        Args:
            user_id: User ID

        Returns:
            Workload statistics dictionary
        """
        domain = [
            ("user_ids", "in", [user_id]),
        ]

        # Note: planned_hours/remaining_hours/kanban_state don't exist in Odoo 18 base project
        # Using allocated_hours and state from base project module
        tasks = self.client.search_read(
            self.model,
            domain,
            fields=[
                "id",
                "name",
                "allocated_hours",
                "priority",
                "date_deadline",
                "state",
            ],
        )

        today = date.today()
        overdue_count = 0
        for task in tasks:
            if task.get("date_deadline"):
                deadline = datetime.fromisoformat(task["date_deadline"]).date()
                if deadline < today:
                    overdue_count += 1

        # Count blocked tasks using state field instead of kanban_state
        blocked_count = sum(
            1 for t in tasks if t.get("state") in ("1_blocked", "blocked")
        )

        return {
            "user_id": user_id,
            "total_tasks": len(tasks),
            "total_planned_hours": sum(t.get("allocated_hours") or 0 for t in tasks),
            "total_remaining_hours": sum(t.get("allocated_hours") or 0 for t in tasks),
            "high_priority_count": sum(
                1 for t in tasks if t.get("priority") in ("2", "3")
            ),
            "blocked_count": blocked_count,
            "overdue_count": overdue_count,
            "tasks": tasks,
        }

    def assign_task(self, task_id: int, user_ids: List[int]) -> bool:
        """
        Assign task to users.

        Args:
            task_id: Task ID
            user_ids: List of user IDs to assign

        Returns:
            True if successful
        """
        # Verify task exists
        self.get_task_by_id(task_id)

        result = self.client.write(
            self.model,
            [task_id],
            {
                "user_ids": [(6, 0, user_ids)],  # Replace all assignees
                "date_assign": datetime.now().isoformat(),
            },
        )

        logger.info(f"Assigned task {task_id} to users {user_ids}")
        return result

    def update_task(self, task_id: int, values: Dict) -> bool:
        """
        Update task fields.

        Args:
            task_id: Task ID
            values: Fields to update

        Returns:
            True if successful
        """
        # Verify task exists
        self.get_task_by_id(task_id)

        return self.client.write(self.model, [task_id], values)

    def get_completion_rates(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        project_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get task completion statistics for a period.

        Args:
            start_date: Period start (default: 30 days ago)
            end_date: Period end (default: today)
            project_id: Optional project filter

        Returns:
            Completion statistics
        """
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        base_domain = [("create_date", ">=", start_date.isoformat())]
        if project_id:
            base_domain.append(("project_id", "=", project_id))

        # Total tasks created in period
        total = self.client.search_count(self.model, base_domain)

        # Completed tasks - check by state field if available
        completed_domain = base_domain + [("state", "in", ["1_done", "1_canceled", "done", "cancel"])]
        try:
            completed = self.client.search_count(self.model, completed_domain)
        except Exception:
            # Fallback: count tasks in stages that look like done
            completed = 0

        # On-time completions (completed before or on deadline)
        # This requires fetching and analyzing individual tasks
        completed_tasks = self.client.search_read(
            self.model,
            completed_domain,
            fields=["date_deadline", "write_date"],
            limit=1000,
        )

        on_time = 0
        for task in completed_tasks:
            deadline = task.get("date_deadline")
            completed_date = task.get("write_date")
            if deadline and completed_date:
                deadline_dt = datetime.fromisoformat(deadline).date()
                completed_dt = datetime.fromisoformat(completed_date).date()
                if completed_dt <= deadline_dt:
                    on_time += 1
            elif not deadline:
                # No deadline = considered on time
                on_time += 1

        # Overdue tasks
        overdue_domain = base_domain + [
            ("date_deadline", "<", date.today().isoformat()),
            ("date_deadline", "!=", False),
        ]
        overdue = self.client.search_count(self.model, overdue_domain)

        completion_rate = (completed / total * 100) if total > 0 else 0
        on_time_rate = (on_time / completed * 100) if completed > 0 else 0

        return {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_created": total,
            "completed": completed,
            "on_time": on_time,
            "overdue": overdue,
            "in_progress": total - completed,
            "completion_rate": round(completion_rate, 2),
            "on_time_rate": round(on_time_rate, 2),
        }

    def get_tasks_by_stage(self) -> Dict[str, List[Dict]]:
        """
        Get tasks grouped by stage.

        Returns:
            Dictionary with stage names as keys and task lists as values
        """
        # Get all stages
        stages = self.client.search_read(
            ODOO_MODEL_STAGE,
            [],
            fields=["id", "name", "sequence", "is_closed"],
            order="sequence asc",
        )

        result = {}
        for stage in stages:
            stage_tasks = self.client.search_read(
                self.model,
                [("stage_id", "=", stage["id"])],
                fields=DEFAULT_TASK_FIELDS,
            )
            result[stage["name"]] = {
                "stage_id": stage["id"],
                "is_closed": stage.get("is_closed", False),
                "task_count": len(stage_tasks),
                "tasks": stage_tasks,
            }

        return result

    def get_stage_statistics(self) -> List[Dict]:
        """
        Get statistics for each stage.

        Returns:
            List of stage statistics
        """
        stages = self.client.search_read(
            ODOO_MODEL_STAGE,
            [],
            fields=["id", "name", "sequence", "is_closed"],
            order="sequence asc",
        )

        stats = []
        total_tasks = self.client.search_count(self.model, [])

        for stage in stages:
            count = self.client.search_count(
                self.model,
                [("stage_id", "=", stage["id"])],
            )

            stats.append({
                "stage_id": stage["id"],
                "stage_name": stage["name"],
                "is_closed": stage.get("is_closed", False),
                "task_count": count,
                "percentage": round((count / total_tasks * 100) if total_tasks > 0 else 0, 2),
            })

        return stats
