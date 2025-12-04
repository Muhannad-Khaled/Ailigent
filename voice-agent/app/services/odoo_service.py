"""Odoo XML-RPC Service for Voice Agent."""
import xmlrpc.client
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from loguru import logger

from app.config import settings


class OdooService:
    """Service for interacting with Odoo ERP via XML-RPC."""

    _instance: Optional["OdooService"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.url = settings.ODOO_URL.rstrip("/")
        self.db = settings.ODOO_DB
        self.username = settings.ODOO_USERNAME
        self.password = settings.ODOO_PASSWORD
        self.uid: Optional[int] = None
        self.is_connected: bool = False

        # XML-RPC endpoints
        self.common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

        self._initialized = True

    def connect(self) -> bool:
        """Authenticate with Odoo."""
        try:
            self.uid = self.common.authenticate(
                self.db, self.username, self.password, {}
            )
            if self.uid:
                self.is_connected = True
                logger.info(f"Connected to Odoo as UID: {self.uid}")
                return True
            else:
                logger.error("Odoo authentication failed")
                return False
        except Exception as e:
            logger.error(f"Odoo connection error: {e}")
            return False

    def _execute(self, model: str, method: str, *args, **kwargs) -> Any:
        """Execute an Odoo XML-RPC call."""
        if not self.is_connected:
            self.connect()
        return self.models.execute_kw(
            self.db, self.uid, self.password, model, method, args, kwargs
        )

    # ==================== Employee Operations ====================

    def get_all_employees(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all employees."""
        try:
            employee_ids = self._execute(
                "hr.employee", "search", [], {"limit": limit}
            )
            if not employee_ids:
                return []

            employees = self._execute(
                "hr.employee",
                "read",
                employee_ids,
                {"fields": ["id", "name", "work_email", "job_title", "department_id"]},
            )
            return [
                {
                    "id": emp["id"],
                    "name": emp["name"],
                    "email": emp.get("work_email") or "",
                    "job_title": emp.get("job_title") or "",
                    "department": emp["department_id"][1] if emp.get("department_id") else "",
                }
                for emp in employees
            ]
        except Exception as e:
            logger.error(f"Error getting employees: {e}")
            return []

    def get_employee_by_id(self, employee_id: int) -> Optional[Dict[str, Any]]:
        """Get employee details by ID."""
        try:
            employee_data = self._execute(
                "hr.employee",
                "read",
                [employee_id],
                {"fields": ["id", "name", "work_email", "job_title", "department_id", "parent_id"]},
            )
            if employee_data:
                emp = employee_data[0]
                return {
                    "id": emp["id"],
                    "name": emp["name"],
                    "email": emp.get("work_email") or "",
                    "job_title": emp.get("job_title") or "",
                    "department": emp["department_id"][1] if emp.get("department_id") else "",
                    "manager": emp["parent_id"][1] if emp.get("parent_id") else "",
                }
            return None
        except Exception as e:
            logger.error(f"Error getting employee by ID: {e}")
            return None

    # ==================== Leave Management ====================

    def get_leave_balance(self, employee_id: int) -> List[Dict[str, Any]]:
        """Get leave balances for an employee."""
        try:
            allocation_ids = self._execute(
                "hr.leave.allocation",
                "search",
                [["employee_id", "=", employee_id], ["state", "=", "validate"]],
            )
            if not allocation_ids:
                return []

            allocations = self._execute(
                "hr.leave.allocation",
                "read",
                allocation_ids,
                {"fields": ["holiday_status_id", "number_of_days", "leaves_taken"]},
            )

            return [
                {
                    "leave_type": alloc["holiday_status_id"][1] if alloc.get("holiday_status_id") else "Unknown",
                    "allocated": alloc.get("number_of_days", 0),
                    "taken": alloc.get("leaves_taken", 0),
                    "remaining": alloc.get("number_of_days", 0) - alloc.get("leaves_taken", 0),
                }
                for alloc in allocations
            ]
        except Exception as e:
            logger.error(f"Error getting leave balance: {e}")
            return []

    def get_leave_requests(
        self, employee_id: int, state: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get leave requests for an employee."""
        try:
            domain = [["employee_id", "=", employee_id]]
            if state:
                domain.append(["state", "=", state])

            leave_ids = self._execute("hr.leave", "search", domain)
            if not leave_ids:
                return []

            leaves = self._execute(
                "hr.leave",
                "read",
                leave_ids,
                {"fields": ["id", "holiday_status_id", "date_from", "date_to", "number_of_days", "state", "name"]},
            )

            return [
                {
                    "id": leave["id"],
                    "leave_type": leave["holiday_status_id"][1] if leave.get("holiday_status_id") else "Unknown",
                    "date_from": str(leave.get("date_from", "")),
                    "date_to": str(leave.get("date_to", "")),
                    "days": leave.get("number_of_days", 0),
                    "state": leave.get("state", ""),
                    "reason": leave.get("name") or "",
                }
                for leave in leaves
            ]
        except Exception as e:
            logger.error(f"Error getting leave requests: {e}")
            return []

    # ==================== Payroll ====================

    def get_payslips(self, employee_id: int, limit: int = 6) -> List[Dict[str, Any]]:
        """Get recent payslips for an employee."""
        try:
            payslip_ids = self._execute(
                "hr.payslip",
                "search",
                [["employee_id", "=", employee_id]],
                {"limit": limit, "order": "date_to desc"},
            )
            if not payslip_ids:
                return []

            payslips = self._execute(
                "hr.payslip",
                "read",
                payslip_ids,
                {"fields": ["id", "name", "date_from", "date_to", "state", "net_wage", "basic_wage"]},
            )

            return [
                {
                    "id": ps["id"],
                    "name": ps.get("name", ""),
                    "date_from": str(ps.get("date_from", "")),
                    "date_to": str(ps.get("date_to", "")),
                    "state": ps.get("state", ""),
                    "net_wage": ps.get("net_wage", 0),
                    "gross_wage": ps.get("basic_wage", 0),
                }
                for ps in payslips
            ]
        except Exception as e:
            logger.error(f"Error getting payslips: {e}")
            return []

    # ==================== Attendance ====================

    def get_attendance_summary(
        self, employee_id: int, month: Optional[int] = None, year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get attendance summary for an employee."""
        try:
            if not month:
                month = datetime.now().month
            if not year:
                year = datetime.now().year

            first_day = date(year, month, 1)
            if month == 12:
                last_day = date(year + 1, 1, 1)
            else:
                last_day = date(year, month + 1, 1)

            attendance_ids = self._execute(
                "hr.attendance",
                "search",
                [
                    ["employee_id", "=", employee_id],
                    ["check_in", ">=", str(first_day)],
                    ["check_in", "<", str(last_day)],
                ],
            )

            if not attendance_ids:
                return {
                    "month": month,
                    "year": year,
                    "total_days": 0,
                    "total_hours": 0,
                }

            attendances = self._execute(
                "hr.attendance",
                "read",
                attendance_ids,
                {"fields": ["check_in", "check_out", "worked_hours"]},
            )

            total_hours = sum(att.get("worked_hours", 0) for att in attendances)

            return {
                "month": month,
                "year": year,
                "total_days": len(attendances),
                "total_hours": round(total_hours, 2),
            }
        except Exception as e:
            logger.error(f"Error getting attendance: {e}")
            return {"month": month, "year": year, "total_days": 0, "total_hours": 0}

    # ==================== Tasks ====================

    def get_employee_tasks(self, employee_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get tasks assigned to an employee."""
        try:
            task_ids = self._execute(
                "project.task",
                "search",
                [["user_ids", "in", [employee_id]]],
                {"limit": limit},
            )

            if not task_ids:
                return []

            tasks = self._execute(
                "project.task",
                "read",
                task_ids,
                {"fields": ["id", "name", "description", "date_deadline", "priority", "stage_id", "project_id"]},
            )

            return [
                {
                    "id": task["id"],
                    "name": task["name"],
                    "description": task.get("description") or "",
                    "deadline": str(task.get("date_deadline") or ""),
                    "priority": task.get("priority", "0"),
                    "stage": task["stage_id"][1] if task.get("stage_id") else "",
                    "project": task["project_id"][1] if task.get("project_id") else "",
                }
                for task in tasks
            ]
        except Exception as e:
            logger.warning(f"Could not fetch tasks: {e}")
            return []

    def get_all_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all tasks (for team view)."""
        try:
            task_ids = self._execute(
                "project.task",
                "search",
                [],
                {"limit": limit, "order": "date_deadline asc"},
            )

            if not task_ids:
                return []

            tasks = self._execute(
                "project.task",
                "read",
                task_ids,
                {"fields": ["id", "name", "date_deadline", "priority", "stage_id", "project_id", "user_ids"]},
            )

            return [
                {
                    "id": task["id"],
                    "name": task["name"],
                    "deadline": str(task.get("date_deadline") or ""),
                    "priority": task.get("priority", "0"),
                    "stage": task["stage_id"][1] if task.get("stage_id") else "",
                    "project": task["project_id"][1] if task.get("project_id") else "",
                    "assigned_to": task.get("user_ids", []),
                }
                for task in tasks
            ]
        except Exception as e:
            logger.warning(f"Could not fetch tasks: {e}")
            return []

    def get_overdue_tasks(self) -> List[Dict[str, Any]]:
        """Get overdue tasks."""
        try:
            today = date.today().isoformat()
            task_ids = self._execute(
                "project.task",
                "search",
                [
                    ["date_deadline", "<", today],
                    ["stage_id.is_closed", "=", False],
                ],
                {"limit": 50},
            )

            if not task_ids:
                return []

            tasks = self._execute(
                "project.task",
                "read",
                task_ids,
                {"fields": ["id", "name", "date_deadline", "project_id", "user_ids"]},
            )

            return [
                {
                    "id": task["id"],
                    "name": task["name"],
                    "deadline": str(task.get("date_deadline") or ""),
                    "project": task["project_id"][1] if task.get("project_id") else "",
                    "assigned_to": task.get("user_ids", []),
                }
                for task in tasks
            ]
        except Exception as e:
            logger.warning(f"Could not fetch overdue tasks: {e}")
            return []


def get_odoo_service() -> OdooService:
    """Get the singleton OdooService instance."""
    service = OdooService()
    if not service.is_connected:
        service.connect()
    return service
