"""Task Management Integration Service."""

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings
from app.core.exceptions import IntegrationError

logger = logging.getLogger(__name__)


class TaskManagementService:
    """Service for integration with Task Management Agent."""

    def __init__(self):
        self.base_url = settings.TASK_MANAGEMENT_URL.rstrip("/")
        self.api_key = settings.TASK_MANAGEMENT_API_KEY
        self.timeout = 30.0

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with API key."""
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to task management API."""
        url = f"{self.base_url}{endpoint}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self._get_headers(),
                    json=data,
                )
                response.raise_for_status()
                return response.json()

        except httpx.TimeoutException:
            logger.error(f"Timeout connecting to task management at {url}")
            raise IntegrationError(
                "Task management service timeout",
                details={"url": url},
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Task management API error: {e.response.status_code}")
            raise IntegrationError(
                f"Task management API error: {e.response.status_code}",
                details={"url": url, "status": e.response.status_code},
            )
        except Exception as e:
            logger.error(f"Failed to connect to task management: {e}")
            raise IntegrationError(
                "Failed to connect to task management service",
                details={"error": str(e)},
            )

    async def health_check(self) -> Dict[str, Any]:
        """Check task management service health."""
        try:
            return await self._make_request("GET", "/api/v1/health")
        except IntegrationError:
            return {"available": False, "error": "Service unavailable"}

    async def create_task(
        self,
        name: str,
        description: str,
        user_ids: List[int],
        project_id: Optional[int] = None,
        priority: str = "normal",
        deadline: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a task in task management system."""
        data = {
            "name": name,
            "description": description,
            "user_ids": user_ids,
            "priority": priority,
        }

        if project_id:
            data["project_id"] = project_id
        if deadline:
            data["deadline"] = deadline

        return await self._make_request("POST", "/api/v1/tasks", data)

    async def create_onboarding_tasks(
        self,
        employee_id: int,
        employee_name: str,
        manager_id: int,
        department: str,
    ) -> List[Dict[str, Any]]:
        """Create onboarding tasks for a new hire."""
        onboarding_tasks = [
            {
                "name": f"Complete IT setup for {employee_name}",
                "description": f"Set up computer, email, and system access for new employee {employee_name}",
                "user_ids": [],  # Would need IT team IDs
                "priority": "high",
            },
            {
                "name": f"Schedule orientation for {employee_name}",
                "description": f"Arrange HR orientation session for {employee_name}",
                "user_ids": [],  # Would need HR team IDs
                "priority": "high",
            },
            {
                "name": f"Manager onboarding meeting with {employee_name}",
                "description": f"Schedule initial 1:1 with new team member {employee_name}",
                "user_ids": [manager_id],
                "priority": "normal",
            },
            {
                "name": f"Complete probation review setup for {employee_name}",
                "description": f"Set up 90-day probation review schedule for {employee_name}",
                "user_ids": [manager_id],
                "priority": "normal",
            },
        ]

        created_tasks = []
        for task in onboarding_tasks:
            try:
                result = await self.create_task(**task)
                created_tasks.append(result)
                logger.info(f"Created onboarding task: {task['name']}")
            except IntegrationError as e:
                logger.warning(f"Failed to create task '{task['name']}': {e}")

        return created_tasks

    async def create_appraisal_tasks(
        self,
        cycle_name: str,
        employees: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Create appraisal tasks for managers."""
        created_tasks = []

        # Group employees by manager
        manager_employees: Dict[int, List[str]] = {}
        for emp in employees:
            manager_id = emp.get("manager_id")
            if manager_id:
                if manager_id not in manager_employees:
                    manager_employees[manager_id] = []
                manager_employees[manager_id].append(emp.get("name", "Unknown"))

        # Create one task per manager
        for manager_id, emp_names in manager_employees.items():
            task = {
                "name": f"Complete {cycle_name} appraisals",
                "description": f"Complete performance appraisals for: {', '.join(emp_names)}",
                "user_ids": [manager_id],
                "priority": "high",
            }

            try:
                result = await self.create_task(**task)
                created_tasks.append(result)
                logger.info(f"Created appraisal task for manager {manager_id}")
            except IntegrationError as e:
                logger.warning(f"Failed to create appraisal task: {e}")

        return created_tasks

    async def create_interview_tasks(
        self,
        applicant_name: str,
        job_title: str,
        interviewer_ids: List[int],
        interview_datetime: str,
    ) -> List[Dict[str, Any]]:
        """Create interview preparation tasks."""
        created_tasks = []

        # Task for each interviewer
        for interviewer_id in interviewer_ids:
            task = {
                "name": f"Prepare for interview: {applicant_name}",
                "description": (
                    f"Review CV and prepare questions for {applicant_name} "
                    f"(Position: {job_title}). Interview scheduled: {interview_datetime}"
                ),
                "user_ids": [interviewer_id],
                "priority": "high",
                "deadline": interview_datetime,
            }

            try:
                result = await self.create_task(**task)
                created_tasks.append(result)
            except IntegrationError as e:
                logger.warning(f"Failed to create interview task: {e}")

        return created_tasks

    async def get_employee_tasks(
        self,
        employee_id: int,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get tasks assigned to an employee."""
        endpoint = f"/api/v1/tasks?user_id={employee_id}"
        if status:
            endpoint += f"&status={status}"

        try:
            result = await self._make_request("GET", endpoint)
            return result.get("items", [])
        except IntegrationError:
            return []


_service: Optional[TaskManagementService] = None


def get_task_management_service() -> TaskManagementService:
    """Get the singleton task management service."""
    global _service
    if _service is None:
        _service = TaskManagementService()
    return _service
