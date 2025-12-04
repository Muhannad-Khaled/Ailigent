"""Employee Service - Odoo Integration for HR Reports."""

import logging
import uuid
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from app.config import settings
from app.core.constants import (
    ODOO_MODEL_CONTRACT,
    ODOO_MODEL_DEPARTMENT,
    ODOO_MODEL_EMPLOYEE,
)
from app.services.odoo.client import get_odoo_client

logger = logging.getLogger(__name__)


class EmployeeService:
    """Service for employee and HR reporting operations."""

    def __init__(self):
        self.client = get_odoo_client()
        self._reports: Dict[str, Dict] = {}  # In-memory report cache

    def get_headcount_report(
        self, as_of_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Generate headcount report."""
        report_date = as_of_date or date.today()

        # Total employees
        total = self.client.search_count(ODOO_MODEL_EMPLOYEE, [])
        active = self.client.search_count(ODOO_MODEL_EMPLOYEE, [("active", "=", True)])

        # By department
        by_department = self.get_headcount_by_department(as_of_date)

        # By job title
        employees = self.client.search_read(
            ODOO_MODEL_EMPLOYEE,
            [("active", "=", True)],
            fields=["job_id"],
        )
        job_counts = {}
        for emp in employees:
            if emp.get("job_id"):
                job_name = emp["job_id"][1]
                job_counts[job_name] = job_counts.get(job_name, 0) + 1

        by_job = [
            {"job_title": job, "count": count}
            for job, count in sorted(job_counts.items(), key=lambda x: -x[1])
        ]

        # New hires this month
        month_start = report_date.replace(day=1)
        # Note: hr.employee doesn't have standard entry_date, depends on Odoo config
        new_hires = 0
        terminations = 0

        return {
            "report_date": report_date,
            "total_employees": total,
            "active_employees": active,
            "by_department": by_department,
            "by_job_title": by_job,
            "new_hires_this_month": new_hires,
            "terminations_this_month": terminations,
            "net_change": new_hires - terminations,
        }

    def get_headcount_by_department(
        self, as_of_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Get headcount breakdown by department."""
        departments = self.client.search_read(
            ODOO_MODEL_DEPARTMENT,
            [],
            fields=["id", "name", "manager_id"],
        )

        result = []
        for dept in departments:
            count = self.client.search_count(
                ODOO_MODEL_EMPLOYEE,
                [("department_id", "=", dept["id"]), ("active", "=", True)],
            )
            result.append({
                "department_id": dept["id"],
                "department_name": dept["name"],
                "manager_name": dept["manager_id"][1] if dept.get("manager_id") else None,
                "employee_count": count,
            })

        return sorted(result, key=lambda x: -x["employee_count"])

    def get_turnover_report(
        self,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Generate turnover analytics report."""
        end_date = period_end or date.today()
        start_date = period_start or (end_date - timedelta(days=365))

        # This is a placeholder - actual implementation depends on Odoo's
        # tracking of employee departures (often via hr.contract or custom fields)
        return {
            "period_start": start_date,
            "period_end": end_date,
            "total_terminations": 0,
            "voluntary_terminations": 0,
            "involuntary_terminations": 0,
            "turnover_rate": 0.0,
            "by_department": [],
            "by_tenure": [],
            "trends": [],
        }

    def get_turnover_trends(self, months: int = 12) -> List[Dict[str, Any]]:
        """Get turnover trends over time."""
        # Placeholder
        return []

    def get_department_report(self, department_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed metrics for a specific department."""
        departments = self.client.search_read(
            ODOO_MODEL_DEPARTMENT,
            [("id", "=", department_id)],
            fields=["id", "name", "manager_id"],
        )

        if not departments:
            return None

        dept = departments[0]

        # Count employees
        headcount = self.client.search_count(
            ODOO_MODEL_EMPLOYEE,
            [("department_id", "=", department_id), ("active", "=", True)],
        )

        # Get job positions count
        # Note: In Odoo 18, hr.job doesn't have 'state' field, use 'active' instead
        from app.core.constants import ODOO_MODEL_JOB
        if self.client.is_model_available(ODOO_MODEL_JOB):
            open_positions = self.client.search_count(
                ODOO_MODEL_JOB,
                [("department_id", "=", department_id), ("active", "=", True)],
            )
        else:
            open_positions = 0

        return {
            "department_id": dept["id"],
            "department_name": dept["name"],
            "report_date": date.today(),
            "headcount": headcount,
            "manager_name": dept["manager_id"][1] if dept.get("manager_id") else None,
            "avg_tenure_months": 0,  # Would need employee start dates
            "new_hires_ytd": 0,
            "terminations_ytd": 0,
            "open_positions": open_positions,
            "pending_leave_requests": 0,
            "avg_attendance_rate": None,
        }

    def generate_custom_report(
        self,
        report_type: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        department_ids: Optional[List[int]] = None,
        include_ai_insights: bool = True,
    ) -> Dict[str, Any]:
        """Generate a custom report and store it."""
        report_id = str(uuid.uuid4())[:8]

        report_data = {
            "id": report_id,
            "report_type": report_type,
            "generated_at": date.today().isoformat(),
            "parameters": {
                "date_from": date_from.isoformat() if date_from else None,
                "date_to": date_to.isoformat() if date_to else None,
                "department_ids": department_ids,
                "include_ai_insights": include_ai_insights,
            },
            "status": "completed",
            "data": {},
        }

        # Generate report based on type
        if report_type == "headcount":
            report_data["data"] = self.get_headcount_report(date_from)
        elif report_type == "turnover":
            report_data["data"] = self.get_turnover_report(date_from, date_to)
        elif report_type == "department" and department_ids:
            report_data["data"] = self.get_department_report(department_ids[0])
        else:
            raise ValueError(f"Unknown report type: {report_type}")

        # Store report
        self._reports[report_id] = report_data

        return {
            "id": report_id,
            "report_type": report_type,
            "generated_at": report_data["generated_at"],
            "parameters": report_data["parameters"],
            "status": "completed",
        }

    def get_report_by_id(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get a stored report by ID."""
        return self._reports.get(report_id)

    def list_reports(
        self, report_type: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """List stored reports."""
        reports = list(self._reports.values())

        if report_type:
            reports = [r for r in reports if r["report_type"] == report_type]

        # Sort by generated_at desc
        reports.sort(key=lambda x: x.get("generated_at", ""), reverse=True)

        return [
            {
                "id": r["id"],
                "report_type": r["report_type"],
                "generated_at": r["generated_at"],
                "parameters": r["parameters"],
                "status": r["status"],
            }
            for r in reports[:limit]
        ]

    def export_report_to_pdf(self, report_id: str) -> Optional[bytes]:
        """Export report to PDF."""
        report = self._reports.get(report_id)
        if not report:
            return None

        # Placeholder - would use reportlab or weasyprint
        from app.services.document.report_exporter import generate_pdf_report
        return generate_pdf_report(report)

    def export_report_to_excel(self, report_id: str) -> Optional[bytes]:
        """Export report to Excel."""
        report = self._reports.get(report_id)
        if not report:
            return None

        # Placeholder - would use openpyxl
        from app.services.document.report_exporter import generate_excel_report
        return generate_excel_report(report)


_service: Optional[EmployeeService] = None


def get_employee_service() -> EmployeeService:
    """Get the singleton employee service."""
    global _service
    if _service is None:
        _service = EmployeeService()
    return _service
