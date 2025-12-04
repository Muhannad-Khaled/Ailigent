"""Appraisal Service - Odoo Integration for Performance Appraisals."""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from app.config import settings
from app.core.constants import (
    ODOO_MODEL_APPRAISAL,
    ODOO_MODEL_APPRAISAL_GOAL,
    ODOO_MODEL_EMPLOYEE,
)
from app.core.exceptions import AppraisalNotFoundError, OdooModuleNotFoundError
from app.services.odoo.client import get_odoo_client

logger = logging.getLogger(__name__)


class AppraisalService:
    """Service for appraisal operations via Odoo."""

    def __init__(self):
        self.client = get_odoo_client()
        self._last_reminder_run = None
        self._reminders_sent = 0

    def _ensure_appraisal_module(self):
        """Ensure appraisal module is available."""
        if not self.client.is_model_available(ODOO_MODEL_APPRAISAL):
            raise OdooModuleNotFoundError(
                "HR Appraisal module (hr_appraisal) is not installed in Odoo",
                details={"model": ODOO_MODEL_APPRAISAL},
            )

    def get_cycles(self, state: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get appraisal cycles."""
        self._ensure_appraisal_module()

        # Note: Odoo doesn't have a separate cycle model in standard hr_appraisal
        # This is a simplified implementation - may need customization per Odoo setup
        domain = []
        if state:
            domain.append(("state", "=", state))

        # Group appraisals by date_close to simulate cycles
        appraisals = self.client.search_read(
            ODOO_MODEL_APPRAISAL,
            domain,
            fields=["id", "date_close", "state"],
        )

        # For now, return empty as this depends on Odoo customization
        return []

    def get_cycle_by_id(self, cycle_id: int) -> Optional[Dict[str, Any]]:
        """Get cycle by ID."""
        self._ensure_appraisal_module()
        # Placeholder - depends on Odoo customization
        return None

    def get_cycle_status(self, cycle_id: int) -> Dict[str, Any]:
        """Get completion status for a cycle."""
        self._ensure_appraisal_module()
        # Placeholder
        return {
            "cycle_id": cycle_id,
            "total": 0,
            "completed": 0,
            "pending": 0,
            "completion_rate": 0,
        }

    def get_appraisals(
        self,
        filters: Any,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Get appraisals with filters."""
        self._ensure_appraisal_module()

        domain = []
        if filters.employee_id:
            domain.append(("employee_id", "=", filters.employee_id))
        if filters.manager_id:
            domain.append(("manager_id", "=", filters.manager_id))
        if filters.department_id:
            domain.append(("department_id", "=", filters.department_id))
        if filters.state:
            domain.append(("state", "=", filters.state))

        total = self.client.search_count(ODOO_MODEL_APPRAISAL, domain)

        appraisals = self.client.search_read(
            ODOO_MODEL_APPRAISAL,
            domain,
            fields=[
                "id", "employee_id", "manager_id", "department_id",
                "date_close", "state", "create_date"
            ],
            limit=page_size,
            offset=(page - 1) * page_size,
            order="create_date desc",
        )

        items = [
            {
                "id": app["id"],
                "employee_id": app["employee_id"][0] if app.get("employee_id") else None,
                "employee_name": app["employee_id"][1] if app.get("employee_id") else "Unknown",
                "manager_id": app["manager_id"][0] if app.get("manager_id") else None,
                "manager_name": app["manager_id"][1] if app.get("manager_id") else None,
                "department_id": app["department_id"][0] if app.get("department_id") else None,
                "department_name": app["department_id"][1] if app.get("department_id") else None,
                "date_close": app.get("date_close"),
                "state": app.get("state", "new"),
                "create_date": app.get("create_date"),
            }
            for app in appraisals
        ]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    def get_pending_appraisals(
        self,
        manager_id: Optional[int] = None,
        department_id: Optional[int] = None,
        days_until_deadline: int = 30,
    ) -> List[Dict[str, Any]]:
        """Get pending appraisals requiring action."""
        self._ensure_appraisal_module()

        domain = [("state", "in", ["new", "pending"])]

        if manager_id:
            domain.append(("manager_id", "=", manager_id))
        if department_id:
            domain.append(("department_id", "=", department_id))

        # Filter by deadline
        deadline = date.today() + timedelta(days=days_until_deadline)
        domain.append(("date_close", "<=", deadline.isoformat()))

        appraisals = self.client.search_read(
            ODOO_MODEL_APPRAISAL,
            domain,
            fields=[
                "id", "employee_id", "manager_id", "department_id",
                "date_close", "state", "create_date"
            ],
            order="date_close asc",
        )

        return [
            {
                "id": app["id"],
                "employee_id": app["employee_id"][0] if app.get("employee_id") else None,
                "employee_name": app["employee_id"][1] if app.get("employee_id") else "Unknown",
                "manager_id": app["manager_id"][0] if app.get("manager_id") else None,
                "manager_name": app["manager_id"][1] if app.get("manager_id") else None,
                "department_id": app["department_id"][0] if app.get("department_id") else None,
                "department_name": app["department_id"][1] if app.get("department_id") else None,
                "date_close": app.get("date_close"),
                "state": app.get("state", "new"),
                "create_date": app.get("create_date"),
            }
            for app in appraisals
        ]

    def get_appraisal_by_id(self, appraisal_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed appraisal with goals and notes."""
        self._ensure_appraisal_module()

        appraisals = self.client.search_read(
            ODOO_MODEL_APPRAISAL,
            [("id", "=", appraisal_id)],
            fields=[
                "id", "employee_id", "manager_id", "department_id",
                "date_close", "state", "create_date", "note"
            ],
        )

        if not appraisals:
            return None

        app = appraisals[0]

        # Get goals if model exists
        goals = []
        if self.client.is_model_available(ODOO_MODEL_APPRAISAL_GOAL):
            goal_records = self.client.search_read(
                ODOO_MODEL_APPRAISAL_GOAL,
                [("employee_id", "=", app["employee_id"][0] if app.get("employee_id") else 0)],
                fields=["id", "name", "description", "deadline", "progression", "employee_id"],
            )
            goals = [
                {
                    "id": g["id"],
                    "name": g["name"],
                    "description": g.get("description"),
                    "deadline": g.get("deadline"),
                    "progression": g.get("progression", 0),
                    "employee_id": g["employee_id"][0] if g.get("employee_id") else None,
                    "employee_name": g["employee_id"][1] if g.get("employee_id") else None,
                }
                for g in goal_records
            ]

        # Notes would come from appraisal.note or hr.appraisal.note model
        notes = []
        if app.get("note"):
            notes = [
                {
                    "id": 0,
                    "note": app["note"],
                    "author_id": app["manager_id"][0] if app.get("manager_id") else 0,
                    "author_name": app["manager_id"][1] if app.get("manager_id") else "Unknown",
                    "date": app.get("create_date"),
                }
            ]

        return {
            "id": app["id"],
            "employee_id": app["employee_id"][0] if app.get("employee_id") else None,
            "employee_name": app["employee_id"][1] if app.get("employee_id") else "Unknown",
            "manager_id": app["manager_id"][0] if app.get("manager_id") else None,
            "manager_name": app["manager_id"][1] if app.get("manager_id") else None,
            "department_id": app["department_id"][0] if app.get("department_id") else None,
            "department_name": app["department_id"][1] if app.get("department_id") else None,
            "date_close": app.get("date_close"),
            "state": app.get("state", "new"),
            "create_date": app.get("create_date"),
            "goals": goals,
            "notes": notes,
            "ai_summary": None,
        }

    def get_appraisals_by_employee(self, employee_id: int) -> List[Dict[str, Any]]:
        """Get all appraisals for an employee."""
        self._ensure_appraisal_module()

        appraisals = self.client.search_read(
            ODOO_MODEL_APPRAISAL,
            [("employee_id", "=", employee_id)],
            fields=[
                "id", "employee_id", "manager_id", "department_id",
                "date_close", "state", "create_date"
            ],
            order="date_close desc",
        )

        return [
            {
                "id": app["id"],
                "employee_id": app["employee_id"][0] if app.get("employee_id") else None,
                "employee_name": app["employee_id"][1] if app.get("employee_id") else "Unknown",
                "manager_id": app["manager_id"][0] if app.get("manager_id") else None,
                "manager_name": app["manager_id"][1] if app.get("manager_id") else None,
                "department_id": app["department_id"][0] if app.get("department_id") else None,
                "department_name": app["department_id"][1] if app.get("department_id") else None,
                "date_close": app.get("date_close"),
                "state": app.get("state", "new"),
                "create_date": app.get("create_date"),
            }
            for app in appraisals
        ]

    def update_appraisal_summary(
        self, appraisal_id: int, summary: Dict[str, Any]
    ) -> bool:
        """Store AI summary for an appraisal."""
        self._ensure_appraisal_module()

        # Store summary in note field
        summary_text = f"""
AI Summary:
{summary.get('executive_summary', '')}

Key Strengths: {', '.join(summary.get('key_strengths', []))}
Areas for Improvement: {', '.join(summary.get('areas_for_improvement', []))}
Rating Suggestion: {summary.get('overall_rating_suggestion', 'N/A')}
"""
        return self.client.write(
            ODOO_MODEL_APPRAISAL,
            [appraisal_id],
            {"note": summary_text},
        )

    def send_reminders(
        self,
        appraisal_ids: Optional[List[int]] = None,
        days_until_deadline: int = 7,
    ) -> Dict[str, Any]:
        """Send reminders for pending appraisals."""
        self._ensure_appraisal_module()

        # Get pending appraisals
        if appraisal_ids:
            domain = [("id", "in", appraisal_ids), ("state", "in", ["new", "pending"])]
        else:
            deadline = date.today() + timedelta(days=days_until_deadline)
            domain = [
                ("state", "in", ["new", "pending"]),
                ("date_close", "<=", deadline.isoformat()),
            ]

        appraisals = self.client.search_read(
            ODOO_MODEL_APPRAISAL,
            domain,
            fields=["id", "employee_id", "manager_id", "date_close"],
        )

        # Send reminders (placeholder - would integrate with notification service)
        reminder_count = len(appraisals)
        self._last_reminder_run = datetime.now()
        self._reminders_sent = reminder_count

        return {"count": reminder_count}

    def get_reminder_status(self) -> Dict[str, Any]:
        """Get status of reminder job."""
        return {
            "last_run": self._last_reminder_run,
            "reminders_sent": self._reminders_sent,
            "next_run": None,  # Would come from scheduler
            "status": "active" if self._last_reminder_run else "never_run",
        }


_service: Optional[AppraisalService] = None


def get_appraisal_service() -> AppraisalService:
    """Get the singleton appraisal service."""
    global _service
    if _service is None:
        _service = AppraisalService()
    return _service
