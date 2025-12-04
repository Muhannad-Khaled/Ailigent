"""Attendance Service - Odoo Integration for Attendance and Leave."""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from app.config import settings
from app.core.constants import (
    ODOO_MODEL_ATTENDANCE,
    ODOO_MODEL_DEPARTMENT,
    ODOO_MODEL_EMPLOYEE,
    ODOO_MODEL_LEAVE,
    ODOO_MODEL_LEAVE_ALLOCATION,
    ODOO_MODEL_LEAVE_TYPE,
)
from app.core.exceptions import LeaveRequestNotFoundError, OdooModuleNotFoundError
from app.services.odoo.client import get_odoo_client

logger = logging.getLogger(__name__)


class AttendanceService:
    """Service for attendance and leave operations."""

    def __init__(self):
        self.client = get_odoo_client()

    def _ensure_attendance_module(self):
        """Ensure attendance module is available."""
        if not self.client.is_model_available(ODOO_MODEL_ATTENDANCE):
            raise OdooModuleNotFoundError(
                "HR Attendance module (hr_attendance) is not installed in Odoo",
                details={"model": ODOO_MODEL_ATTENDANCE},
            )

    def _ensure_leave_module(self):
        """Ensure leave/holidays module is available."""
        if not self.client.is_model_available(ODOO_MODEL_LEAVE):
            raise OdooModuleNotFoundError(
                "HR Leave/Holidays module (hr_holidays) is not installed in Odoo",
                details={"model": ODOO_MODEL_LEAVE},
            )

    # ==================
    # Leave Management
    # ==================

    def get_pending_leave_requests(
        self,
        department_id: Optional[int] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get pending leave requests."""
        self._ensure_leave_module()

        domain = [("state", "=", "confirm")]  # Awaiting approval
        if department_id:
            domain.append(("department_id", "=", department_id))

        leaves = self.client.search_read(
            ODOO_MODEL_LEAVE,
            domain,
            fields=[
                "id", "employee_id", "department_id", "holiday_status_id",
                "date_from", "date_to", "number_of_days", "state", "create_date", "name"
            ],
            limit=limit,
            order="create_date desc",
        )

        return [
            {
                "id": leave["id"],
                "employee_id": leave["employee_id"][0] if leave.get("employee_id") else None,
                "employee_name": leave["employee_id"][1] if leave.get("employee_id") else "Unknown",
                "department_id": leave["department_id"][0] if leave.get("department_id") else None,
                "department_name": leave["department_id"][1] if leave.get("department_id") else None,
                "leave_type_id": leave["holiday_status_id"][0] if leave.get("holiday_status_id") else None,
                "leave_type_name": leave["holiday_status_id"][1] if leave.get("holiday_status_id") else "Unknown",
                "date_from": leave.get("date_from"),
                "date_to": leave.get("date_to"),
                "number_of_days": leave.get("number_of_days", 0),
                "state": leave.get("state"),
                "request_date": leave.get("create_date"),
                "notes": leave.get("name"),
            }
            for leave in leaves
        ]

    def approve_leave(self, leave_id: int, notes: Optional[str] = None) -> bool:
        """Approve a leave request."""
        self._ensure_leave_module()

        # Verify leave exists and is pending
        leaves = self.client.search_read(
            ODOO_MODEL_LEAVE,
            [("id", "=", leave_id)],
            fields=["id", "state"],
        )

        if not leaves:
            raise LeaveRequestNotFoundError(f"Leave request {leave_id} not found")

        if leaves[0]["state"] not in ["confirm", "validate1"]:
            raise ValueError(f"Leave request is not pending approval (state: {leaves[0]['state']})")

        # Call action_approve method
        try:
            self.client.execute_kw(
                ODOO_MODEL_LEAVE,
                "action_approve",
                [[leave_id]],
            )
            return True
        except Exception as e:
            # Fallback to direct state update
            return self.client.write(
                ODOO_MODEL_LEAVE,
                [leave_id],
                {"state": "validate"},
            )

    def reject_leave(self, leave_id: int, notes: Optional[str] = None) -> bool:
        """Reject a leave request."""
        self._ensure_leave_module()

        leaves = self.client.search_read(
            ODOO_MODEL_LEAVE,
            [("id", "=", leave_id)],
            fields=["id", "state"],
        )

        if not leaves:
            raise LeaveRequestNotFoundError(f"Leave request {leave_id} not found")

        try:
            self.client.execute_kw(
                ODOO_MODEL_LEAVE,
                "action_refuse",
                [[leave_id]],
            )
            return True
        except Exception:
            return self.client.write(
                ODOO_MODEL_LEAVE,
                [leave_id],
                {"state": "refuse"},
            )

    def create_leave_request(
        self,
        employee_id: int,
        leave_type_id: int,
        date_from: date,
        date_to: date,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new leave request (for demo purposes)."""
        self._ensure_leave_module()

        # Get employee info
        employees = self.client.search_read(
            ODOO_MODEL_EMPLOYEE,
            [("id", "=", employee_id)],
            fields=["id", "name", "department_id"],
        )
        if not employees:
            raise ValueError(f"Employee {employee_id} not found")

        employee = employees[0]

        # Get leave type info
        leave_types = self.client.search_read(
            ODOO_MODEL_LEAVE_TYPE,
            [("id", "=", leave_type_id)],
            fields=["id", "name"],
        )
        if not leave_types:
            raise ValueError(f"Leave type {leave_type_id} not found")

        leave_type = leave_types[0]

        # Create leave request with state 'confirm' (pending approval)
        values = {
            "employee_id": employee_id,
            "holiday_status_id": leave_type_id,
            "date_from": datetime.combine(date_from, datetime.min.time()).isoformat(),
            "date_to": datetime.combine(date_to, datetime.max.time()).isoformat(),
            "request_date_from": date_from.isoformat(),
            "request_date_to": date_to.isoformat(),
            "name": notes or f"Leave request for {employee['name']}",
        }

        leave_id = self.client.create(ODOO_MODEL_LEAVE, values)

        # Try to confirm the leave request to put it in pending state
        try:
            self.client.execute_kw(
                ODOO_MODEL_LEAVE,
                "action_confirm",
                [[leave_id]],
            )
        except Exception as e:
            logger.warning(f"Could not auto-confirm leave request: {e}")

        # Get the created leave to return full info
        created_leave = self.client.search_read(
            ODOO_MODEL_LEAVE,
            [("id", "=", leave_id)],
            fields=[
                "id", "employee_id", "department_id", "holiday_status_id",
                "date_from", "date_to", "number_of_days", "state", "name"
            ],
        )[0]

        return {
            "id": created_leave["id"],
            "employee_id": employee_id,
            "employee_name": employee["name"],
            "department_id": employee["department_id"][0] if employee.get("department_id") else None,
            "department_name": employee["department_id"][1] if employee.get("department_id") else None,
            "leave_type_id": leave_type_id,
            "leave_type_name": leave_type["name"],
            "date_from": created_leave.get("date_from"),
            "date_to": created_leave.get("date_to"),
            "number_of_days": created_leave.get("number_of_days", 0),
            "state": created_leave.get("state"),
            "notes": created_leave.get("name"),
        }

    def get_leave_balance_report(
        self, department_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get leave balances by department."""
        self._ensure_leave_module()

        # Get departments
        dept_domain = []
        if department_id:
            dept_domain.append(("id", "=", department_id))

        departments = self.client.search_read(
            ODOO_MODEL_DEPARTMENT,
            dept_domain,
            fields=["id", "name"],
        )

        result = []
        for dept in departments:
            # Get employees in department
            employees = self.client.search_read(
                ODOO_MODEL_EMPLOYEE,
                [("department_id", "=", dept["id"]), ("active", "=", True)],
                fields=["id", "name"],
            )

            balances = []
            for emp in employees:
                # Get allocations
                allocations = self.client.search_read(
                    ODOO_MODEL_LEAVE_ALLOCATION,
                    [("employee_id", "=", emp["id"]), ("state", "=", "validate")],
                    fields=["holiday_status_id", "number_of_days", "leaves_taken"],
                )

                for alloc in allocations:
                    balances.append({
                        "employee_id": emp["id"],
                        "employee_name": emp["name"],
                        "leave_type_id": alloc["holiday_status_id"][0] if alloc.get("holiday_status_id") else None,
                        "leave_type_name": alloc["holiday_status_id"][1] if alloc.get("holiday_status_id") else "Unknown",
                        "allocated_days": alloc.get("number_of_days", 0),
                        "taken_days": alloc.get("leaves_taken", 0),
                        "remaining_days": alloc.get("number_of_days", 0) - alloc.get("leaves_taken", 0),
                    })

            # Count pending requests
            pending = self.client.search_count(
                ODOO_MODEL_LEAVE,
                [("department_id", "=", dept["id"]), ("state", "=", "confirm")],
            )

            result.append({
                "department_id": dept["id"],
                "department_name": dept["name"],
                "report_date": date.today(),
                "balances": balances,
                "total_pending_requests": pending,
            })

        return result

    # ==================
    # Attendance Analytics
    # ==================

    def get_summary(self, for_date: Optional[date] = None) -> Dict[str, Any]:
        """Get organization-wide attendance summary."""
        self._ensure_attendance_module()

        check_date = for_date or date.today()
        date_start = datetime.combine(check_date, datetime.min.time())
        date_end = datetime.combine(check_date, datetime.max.time())

        # Total employees
        total_employees = self.client.search_count(
            ODOO_MODEL_EMPLOYEE,
            [("active", "=", True)],
        )

        # Present today
        present_count = self.client.search_count(
            ODOO_MODEL_ATTENDANCE,
            [
                ("check_in", ">=", date_start.isoformat()),
                ("check_in", "<=", date_end.isoformat()),
            ],
        )

        # On leave today
        on_leave = self.client.search_count(
            ODOO_MODEL_LEAVE,
            [
                ("state", "=", "validate"),
                ("date_from", "<=", check_date.isoformat()),
                ("date_to", ">=", check_date.isoformat()),
            ],
        ) if self.client.is_model_available(ODOO_MODEL_LEAVE) else 0

        absent_count = total_employees - present_count - on_leave

        # Get attendance records for average hours
        attendances = self.client.search_read(
            ODOO_MODEL_ATTENDANCE,
            [
                ("check_in", ">=", date_start.isoformat()),
                ("check_in", "<=", date_end.isoformat()),
            ],
            fields=["worked_hours"],
        )

        avg_hours = 0
        if attendances:
            total_hours = sum(a.get("worked_hours", 0) for a in attendances)
            avg_hours = total_hours / len(attendances)

        attendance_rate = (present_count / total_employees * 100) if total_employees > 0 else 0

        return {
            "date": check_date,
            "total_employees": total_employees,
            "present_count": present_count,
            "absent_count": max(0, absent_count),
            "on_leave_count": on_leave,
            "attendance_rate": round(attendance_rate, 2),
            "avg_work_hours": round(avg_hours, 2),
            "late_arrivals": 0,  # Would need expected start time to calculate
            "early_departures": 0,
        }

    def get_department_attendance(
        self,
        department_id: int,
        for_date: Optional[date] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get department attendance summary."""
        self._ensure_attendance_module()

        # Verify department exists
        departments = self.client.search_read(
            ODOO_MODEL_DEPARTMENT,
            [("id", "=", department_id)],
            fields=["id", "name"],
        )

        if not departments:
            return None

        dept = departments[0]
        check_date = for_date or date.today()

        # Get employee IDs in department
        employees = self.client.search(
            ODOO_MODEL_EMPLOYEE,
            [("department_id", "=", department_id), ("active", "=", True)],
        )

        total = len(employees)
        if total == 0:
            return {
                "department_id": dept["id"],
                "department_name": dept["name"],
                "date": check_date,
                "total_employees": 0,
                "present_count": 0,
                "absent_count": 0,
                "on_leave_count": 0,
                "attendance_rate": 0,
            }

        date_start = datetime.combine(check_date, datetime.min.time())
        date_end = datetime.combine(check_date, datetime.max.time())

        # Present
        present = self.client.search_count(
            ODOO_MODEL_ATTENDANCE,
            [
                ("employee_id", "in", employees),
                ("check_in", ">=", date_start.isoformat()),
                ("check_in", "<=", date_end.isoformat()),
            ],
        )

        # On leave
        on_leave = 0
        if self.client.is_model_available(ODOO_MODEL_LEAVE):
            on_leave = self.client.search_count(
                ODOO_MODEL_LEAVE,
                [
                    ("employee_id", "in", employees),
                    ("state", "=", "validate"),
                    ("date_from", "<=", check_date.isoformat()),
                    ("date_to", ">=", check_date.isoformat()),
                ],
            )

        absent = total - present - on_leave

        return {
            "department_id": dept["id"],
            "department_name": dept["name"],
            "date": check_date,
            "total_employees": total,
            "present_count": present,
            "absent_count": max(0, absent),
            "on_leave_count": on_leave,
            "attendance_rate": round(present / total * 100, 2) if total > 0 else 0,
        }

    def get_attendance_for_analysis(
        self,
        days: int = 7,
        department_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get attendance data for AI analysis."""
        self._ensure_attendance_module()

        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        domain = [
            ("check_in", ">=", start_date.isoformat()),
            ("check_in", "<=", end_date.isoformat()),
        ]

        if department_id:
            employees = self.client.search(
                ODOO_MODEL_EMPLOYEE,
                [("department_id", "=", department_id), ("active", "=", True)],
            )
            domain.append(("employee_id", "in", employees))

        attendances = self.client.search_read(
            ODOO_MODEL_ATTENDANCE,
            domain,
            fields=["employee_id", "check_in", "check_out", "worked_hours"],
        )

        return {
            "period_start": start_date,
            "period_end": end_date,
            "records": [
                {
                    "employee_id": a["employee_id"][0] if a.get("employee_id") else None,
                    "employee_name": a["employee_id"][1] if a.get("employee_id") else "Unknown",
                    "check_in": a.get("check_in"),
                    "check_out": a.get("check_out"),
                    "worked_hours": a.get("worked_hours", 0),
                }
                for a in attendances
            ],
        }

    def detect_anomalies_basic(
        self, attendance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Basic rule-based anomaly detection."""
        anomalies = []

        for record in attendance_data.get("records", []):
            # Missing checkout
            if record.get("check_in") and not record.get("check_out"):
                anomalies.append({
                    "employee_id": record["employee_id"],
                    "employee_name": record["employee_name"],
                    "anomaly_type": "missing_checkout",
                    "severity": "medium",
                    "description": f"Missing checkout on {record['check_in'][:10]}",
                    "frequency": "single",
                    "dates_affected": [record["check_in"][:10]],
                    "recommendation": "Verify with employee and update records",
                })

            # Excessive overtime (>12 hours)
            if record.get("worked_hours", 0) > 12:
                anomalies.append({
                    "employee_id": record["employee_id"],
                    "employee_name": record["employee_name"],
                    "anomaly_type": "excessive_overtime",
                    "severity": "high",
                    "description": f"Worked {record['worked_hours']:.1f} hours",
                    "frequency": "single",
                    "dates_affected": [record["check_in"][:10]],
                    "recommendation": "Review workload and consider work-life balance",
                })

        return {
            "analysis_date": date.today(),
            "period_start": attendance_data.get("period_start", date.today()),
            "period_end": attendance_data.get("period_end", date.today()),
            "anomalies": anomalies,
            "summary": {
                "total_anomalies": len(anomalies),
                "high_severity_count": sum(1 for a in anomalies if a["severity"] == "high"),
                "departments_affected": [],
            },
            "department_patterns": [],
            "recommendations": [],
            "overall_assessment": f"Found {len(anomalies)} anomalies in the period.",
        }

    def get_monthly_report(
        self,
        year: int,
        month: int,
        department_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get monthly attendance report."""
        self._ensure_attendance_module()

        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        # Count working days (simple weekday count)
        working_days = sum(
            1 for d in range((end_date - start_date).days + 1)
            if (start_date + timedelta(days=d)).weekday() < 5
        )

        return {
            "year": year,
            "month": month,
            "department_id": department_id,
            "department_name": None,
            "total_working_days": working_days,
            "summary": {},
            "by_employee": [],
            "trends": [],
        }

    def get_department_report(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Get department-wise attendance report."""
        self._ensure_attendance_module()

        departments = self.client.search_read(
            ODOO_MODEL_DEPARTMENT,
            [],
            fields=["id", "name"],
        )

        result = []
        for dept in departments:
            summary = self.get_department_attendance(dept["id"], date_from)
            if summary:
                result.append(summary)

        return result


_service: Optional[AttendanceService] = None


def get_attendance_service() -> AttendanceService:
    """Get the singleton attendance service."""
    global _service
    if _service is None:
        _service = AttendanceService()
    return _service
