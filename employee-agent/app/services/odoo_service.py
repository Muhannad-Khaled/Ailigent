import xmlrpc.client
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from loguru import logger

from app.models.employee import (
    Employee,
    EmployeeLink,
    LeaveBalance,
    LeaveRequest,
    PayslipSummary,
    Task,
)


class OdooService:
    """Service for interacting with Odoo ERP via XML-RPC"""

    def __init__(self, url: str, db: str, username: str, password: str):
        self.url = url.rstrip("/")
        self.db = db
        self.username = username
        self.password = password
        self.uid: Optional[int] = None
        self.is_connected: bool = False

        # XML-RPC endpoints
        self.common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

    async def connect(self) -> bool:
        """Authenticate with Odoo"""
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
        """Execute an Odoo XML-RPC call"""
        return self.models.execute_kw(
            self.db, self.uid, self.password, model, method, args, kwargs
        )

    # ==================== Employee Linking ====================

    async def find_employee_by_email(self, email: str) -> Optional[Employee]:
        """Find an employee by their email address"""
        try:
            logger.info(f"Searching for employee with email: '{email}'")
            # Use ilike for case-insensitive search, trim whitespace
            email = email.strip().lower()
            employee_ids = self._execute(
                "hr.employee",
                "search",
                [["work_email", "ilike", email]],
            )
            logger.info(f"Search result for '{email}': employee_ids={employee_ids}")
            if not employee_ids:
                return None

            employee_data = self._execute(
                "hr.employee",
                "read",
                employee_ids[:1],
                fields=["id", "name", "work_email", "job_title", "department_id", "parent_id", "work_phone", "mobile_phone"],
            )
            if employee_data:
                emp = employee_data[0]
                return Employee(
                    id=emp["id"],
                    name=emp["name"],
                    email=emp.get("work_email"),
                    job_title=emp.get("job_title") or None,
                    department=emp["department_id"][1] if emp.get("department_id") else None,
                    manager_name=emp["parent_id"][1] if emp.get("parent_id") else None,
                    work_phone=emp.get("work_phone") or None,
                    mobile_phone=emp.get("mobile_phone") or None,
                )
            return None
        except Exception as e:
            logger.error(f"Error finding employee by email: {e}")
            return None

    async def get_employee_by_id(self, employee_id: int) -> Optional[Employee]:
        """Get employee details by ID"""
        try:
            employee_data = self._execute(
                "hr.employee",
                "read",
                [employee_id],
                fields=["id", "name", "work_email", "job_title", "department_id", "parent_id", "work_phone", "mobile_phone"],
            )
            if employee_data:
                emp = employee_data[0]
                return Employee(
                    id=emp["id"],
                    name=emp["name"],
                    email=emp.get("work_email"),
                    job_title=emp.get("job_title") or None,
                    department=emp["department_id"][1] if emp.get("department_id") else None,
                    manager_name=emp["parent_id"][1] if emp.get("parent_id") else None,
                    work_phone=emp.get("work_phone") or None,
                    mobile_phone=emp.get("mobile_phone") or None,
                )
            return None
        except Exception as e:
            logger.error(f"Error getting employee by ID: {e}")
            return None

    # ==================== Leave Management ====================

    async def get_leave_balance(self, employee_id: int) -> List[LeaveBalance]:
        """Get leave balances for an employee"""
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
                fields=["holiday_status_id", "number_of_days", "leaves_taken"],
            )

            balances = []
            for alloc in allocations:
                leave_type = alloc["holiday_status_id"][1] if alloc.get("holiday_status_id") else "Unknown"
                allocated = alloc.get("number_of_days", 0)
                taken = alloc.get("leaves_taken", 0)
                balances.append(
                    LeaveBalance(
                        leave_type=leave_type,
                        allocated=allocated,
                        taken=taken,
                        remaining=allocated - taken,
                    )
                )
            return balances
        except Exception as e:
            logger.error(f"Error getting leave balance: {e}")
            return []

    async def get_leave_requests(
        self, employee_id: int, state: Optional[str] = None
    ) -> List[LeaveRequest]:
        """Get leave requests for an employee"""
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
                fields=["id", "holiday_status_id", "date_from", "date_to", "number_of_days", "state", "name"],
            )

            return [
                LeaveRequest(
                    id=leave["id"],
                    leave_type=leave["holiday_status_id"][1] if leave.get("holiday_status_id") else "Unknown",
                    date_from=str(leave.get("date_from", "")),
                    date_to=str(leave.get("date_to", "")),
                    number_of_days=leave.get("number_of_days", 0),
                    state=leave.get("state", ""),
                    reason=leave.get("name"),
                )
                for leave in leaves
            ]
        except Exception as e:
            logger.error(f"Error getting leave requests: {e}")
            return []

    async def create_leave_request(
        self,
        employee_id: int,
        leave_type_id: int,
        date_from: str,
        date_to: str,
        reason: str = "",
    ) -> Optional[int]:
        """Create a new leave request"""
        try:
            leave_id = self._execute(
                "hr.leave",
                "create",
                [{
                    "employee_id": employee_id,
                    "holiday_status_id": leave_type_id,
                    "date_from": date_from,
                    "date_to": date_to,
                    "name": reason,
                }],
            )
            return leave_id
        except Exception as e:
            logger.error(f"Error creating leave request: {e}")
            return None

    # ==================== Payroll ====================

    async def get_payslips(
        self, employee_id: int, limit: int = 6
    ) -> List[PayslipSummary]:
        """Get recent payslips for an employee"""
        try:
            payslip_ids = self._execute(
                "hr.payslip",
                "search",
                [["employee_id", "=", employee_id]],
                limit=limit,
                order="date_to desc",
            )
            if not payslip_ids:
                return []

            payslips = self._execute(
                "hr.payslip",
                "read",
                payslip_ids,
                fields=["id", "name", "date_from", "date_to", "state", "net_wage", "basic_wage"],
            )

            return [
                PayslipSummary(
                    id=ps["id"],
                    name=ps.get("name", ""),
                    date_from=str(ps.get("date_from", "")),
                    date_to=str(ps.get("date_to", "")),
                    state=ps.get("state", ""),
                    net_wage=ps.get("net_wage", 0),
                    gross_wage=ps.get("basic_wage", 0),
                )
                for ps in payslips
            ]
        except Exception as e:
            logger.error(f"Error getting payslips: {e}")
            return []

    # ==================== Attendance ====================

    async def get_attendance_summary(
        self, employee_id: int, month: Optional[int] = None, year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get attendance summary for an employee"""
        try:
            # Convert to int (Gemini may pass floats)
            employee_id = int(employee_id)
            if not month:
                month = datetime.now().month
            else:
                month = int(month)
            if not year:
                year = datetime.now().year
            else:
                year = int(year)

            # Get first and last day of month
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
                    "records": [],
                }

            attendances = self._execute(
                "hr.attendance",
                "read",
                attendance_ids,
                fields=["check_in", "check_out", "worked_hours"],
            )

            total_hours = sum(att.get("worked_hours", 0) for att in attendances)

            return {
                "month": month,
                "year": year,
                "total_days": len(attendances),
                "total_hours": round(total_hours, 2),
                "records": attendances[:10],  # Last 10 records
            }
        except Exception as e:
            logger.error(f"Error getting attendance: {e}")
            return {}

    # ==================== Tasks (using project.task or mail.activity) ====================

    async def get_employee_tasks(self, employee_id: int) -> List[Dict[str, Any]]:
        """Get tasks assigned to an employee"""
        try:
            # Try project.task first (if project module is installed)
            task_ids = self._execute(
                "project.task",
                "search",
                [["user_ids", "in", [employee_id]]],
                limit=20,
            )

            if task_ids:
                tasks = self._execute(
                    "project.task",
                    "read",
                    task_ids,
                    fields=["id", "name", "description", "date_deadline", "priority", "stage_id"],
                )
                return tasks
            return []
        except Exception as e:
            logger.warning(f"Could not fetch tasks (project module may not be installed): {e}")
            return []

    async def create_task(
        self,
        employee_id: int,
        name: str,
        description: str = "",
        due_date: Optional[str] = None,
    ) -> Optional[int]:
        """Create a task for an employee"""
        try:
            task_data = {
                "name": name,
                "description": description,
                "user_ids": [(4, employee_id)],
            }
            if due_date:
                task_data["date_deadline"] = due_date

            task_id = self._execute("project.task", "create", [task_data])
            return task_id
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return None

    # ==================== Company Policies ====================

    async def get_company_policies(self) -> List[Dict[str, Any]]:
        """Get company policies/documents"""
        try:
            # Try to get from hr.policy or documents module
            policy_ids = self._execute(
                "ir.attachment",
                "search",
                [["res_model", "=", "hr.employee"], ["name", "ilike", "policy"]],
                limit=20,
            )

            if policy_ids:
                policies = self._execute(
                    "ir.attachment",
                    "read",
                    policy_ids,
                    fields=["id", "name", "description", "create_date"],
                )
                return policies
            return []
        except Exception as e:
            logger.warning(f"Could not fetch policies: {e}")
            return []

    # ==================== Employee Link Storage ====================
    # Store Telegram-Odoo links in a custom Odoo model or use ir.config_parameter

    async def save_telegram_link(self, telegram_id: int, employee_id: int, telegram_username: str = None) -> bool:
        """Save Telegram-Odoo employee link"""
        try:
            # Store in ir.config_parameter as JSON
            key = f"telegram_link_{telegram_id}"
            value = f"{employee_id}|{telegram_username or ''}"

            existing = self._execute(
                "ir.config_parameter",
                "search",
                [["key", "=", key]],
            )

            if existing:
                self._execute(
                    "ir.config_parameter",
                    "write",
                    existing,
                    {"value": value},
                )
            else:
                self._execute(
                    "ir.config_parameter",
                    "create",
                    [{"key": key, "value": value}],
                )
            return True
        except Exception as e:
            logger.error(f"Error saving telegram link: {e}")
            return False

    async def get_employee_by_telegram(self, telegram_id: int) -> Optional[int]:
        """Get Odoo employee ID from Telegram ID"""
        try:
            key = f"telegram_link_{telegram_id}"
            param_ids = self._execute(
                "ir.config_parameter",
                "search",
                [["key", "=", key]],
            )

            if param_ids:
                param = self._execute(
                    "ir.config_parameter",
                    "read",
                    param_ids[:1],
                    fields=["value"],
                )
                if param:
                    value = param[0].get("value", "")
                    employee_id = int(value.split("|")[0])
                    return employee_id
            return None
        except Exception as e:
            logger.error(f"Error getting telegram link: {e}")
            return None

    async def remove_telegram_link(self, telegram_id: int) -> bool:
        """Remove Telegram-Odoo link"""
        try:
            key = f"telegram_link_{telegram_id}"
            param_ids = self._execute(
                "ir.config_parameter",
                "search",
                [["key", "=", key]],
            )

            if param_ids:
                self._execute("ir.config_parameter", "unlink", param_ids)
            return True
        except Exception as e:
            logger.error(f"Error removing telegram link: {e}")
            return False
