"""HTTP clients for Ailigent backend services."""
from typing import Any, Dict, Optional, List
import httpx
from loguru import logger

from app.config import settings


class BaseServiceClient:
    """Base HTTP client for backend services."""

    def __init__(self, base_url: str, api_key: str = "", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make HTTP request to service."""
        headers = kwargs.pop("headers", {})
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            url = f"{self.base_url}{path}"
            try:
                response = await client.request(method, url, headers=headers, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code}: {e}")
                return {"success": False, "error": f"HTTP {e.response.status_code}"}
            except httpx.RequestError as e:
                logger.error(f"Request error: {e}")
                return {"success": False, "error": str(e)}
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return {"success": False, "error": str(e)}


class TaskServiceClient(BaseServiceClient):
    """HTTP client for task-management service."""

    def __init__(self):
        super().__init__(
            settings.TASK_MANAGEMENT_URL,
            settings.TASK_MANAGEMENT_API_KEY,
        )

    async def get_tasks(
        self,
        page: int = 1,
        page_size: int = 20,
        project_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get tasks list."""
        params = {"page": page, "page_size": page_size}
        if project_id:
            params["project_id"] = project_id
        return await self._request("GET", "/api/v1/tasks", params=params)

    async def get_overdue_tasks(self) -> Dict[str, Any]:
        """Get overdue tasks."""
        return await self._request("GET", "/api/v1/tasks/overdue")

    async def get_task_stages(self) -> Dict[str, Any]:
        """Get task statistics by stage."""
        return await self._request("GET", "/api/v1/tasks/stages")

    async def get_employees_workload(self) -> Dict[str, Any]:
        """Get employees with workload."""
        return await self._request("GET", "/api/v1/employees")

    async def get_distribution_suggestions(self) -> Dict[str, Any]:
        """Get AI-powered task distribution suggestions."""
        return await self._request("POST", "/api/v1/distribution")


class HRServiceClient(BaseServiceClient):
    """HTTP client for hr-agent service."""

    def __init__(self):
        super().__init__(
            settings.HR_AGENT_URL,
            settings.HR_AGENT_API_KEY,
        )

    async def get_pending_leaves(self) -> Dict[str, Any]:
        """Get pending leave requests for approval."""
        return await self._request("GET", "/api/v1/attendance/leave/pending")

    async def approve_leave(self, leave_id: int, notes: str = "") -> Dict[str, Any]:
        """Approve a leave request."""
        return await self._request(
            "POST",
            f"/api/v1/attendance/leave/{leave_id}/approve",
            json={"notes": notes},
        )

    async def reject_leave(self, leave_id: int, notes: str = "") -> Dict[str, Any]:
        """Reject a leave request."""
        return await self._request(
            "POST",
            f"/api/v1/attendance/leave/{leave_id}/reject",
            json={"notes": notes},
        )

    async def get_headcount_report(self) -> Dict[str, Any]:
        """Get headcount report."""
        return await self._request("GET", "/api/v1/reports/headcount")

    async def get_turnover_report(self) -> Dict[str, Any]:
        """Get turnover report."""
        return await self._request("GET", "/api/v1/reports/turnover")

    async def get_hr_insights(self) -> Dict[str, Any]:
        """Get AI-powered HR insights."""
        return await self._request("POST", "/api/v1/reports/insights")

    async def get_pending_appraisals(self, days: int = 7) -> Dict[str, Any]:
        """Get pending appraisals."""
        return await self._request(
            "GET",
            "/api/v1/appraisals/pending",
            params={"days_until_deadline": days},
        )

    async def get_attendance_anomalies(self) -> Dict[str, Any]:
        """Get attendance anomalies."""
        return await self._request("GET", "/api/v1/attendance/anomalies")


class ContractServiceClient(BaseServiceClient):
    """HTTP client for contracts-agent service."""

    def __init__(self):
        super().__init__(
            settings.CONTRACTS_AGENT_URL,
            settings.CONTRACTS_AGENT_API_KEY,
        )

    async def get_contracts(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Get contracts list."""
        return await self._request(
            "GET",
            "/api/v1/contracts",
            params={"page": page, "page_size": page_size},
        )

    async def get_expiring_contracts(self, days: int = 30) -> Dict[str, Any]:
        """Get contracts expiring within specified days."""
        return await self._request(
            "GET",
            "/api/v1/contracts/expiring",
            params={"days": days},
        )

    async def get_contract(self, contract_id: int) -> Dict[str, Any]:
        """Get contract details."""
        return await self._request("GET", f"/api/v1/contracts/{contract_id}")

    async def analyze_contract(self, contract_id: int) -> Dict[str, Any]:
        """Get AI analysis of a contract."""
        return await self._request("POST", f"/api/v1/contracts/{contract_id}/analyze")

    async def get_compliance_report(self) -> Dict[str, Any]:
        """Get compliance report."""
        return await self._request("GET", "/api/v1/reports/compliance")

    async def get_risk_report(self) -> Dict[str, Any]:
        """Get risk assessment report."""
        return await self._request("GET", "/api/v1/reports/risk")


# Singleton instances
_task_client: Optional[TaskServiceClient] = None
_hr_client: Optional[HRServiceClient] = None
_contract_client: Optional[ContractServiceClient] = None


def get_task_client() -> TaskServiceClient:
    """Get task service client singleton."""
    global _task_client
    if _task_client is None:
        _task_client = TaskServiceClient()
    return _task_client


def get_hr_client() -> HRServiceClient:
    """Get HR service client singleton."""
    global _hr_client
    if _hr_client is None:
        _hr_client = HRServiceClient()
    return _hr_client


def get_contract_client() -> ContractServiceClient:
    """Get contract service client singleton."""
    global _contract_client
    if _contract_client is None:
        _contract_client = ContractServiceClient()
    return _contract_client
