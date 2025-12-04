"""Recruitment Service - Odoo Integration for HR Recruitment."""

import base64
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.config import settings
from app.core.constants import (
    ODOO_MODEL_APPLICANT,
    ODOO_MODEL_ATTACHMENT,
    ODOO_MODEL_CALENDAR_EVENT,
    ODOO_MODEL_CANDIDATE,
    ODOO_MODEL_JOB,
    ODOO_MODEL_RECRUITMENT_STAGE,
)
from app.core.exceptions import ApplicantNotFoundError, JobNotFoundError, OdooModuleNotFoundError
from app.services.odoo.client import get_odoo_client

logger = logging.getLogger(__name__)


class RecruitmentService:
    """Service for recruitment operations via Odoo."""

    def __init__(self):
        self.client = get_odoo_client()

    def _ensure_recruitment_module(self):
        """Ensure recruitment module is available."""
        if not self.client.is_model_available(ODOO_MODEL_APPLICANT):
            raise OdooModuleNotFoundError(
                "HR Recruitment module (hr_recruitment) is not installed in Odoo",
                details={"model": ODOO_MODEL_APPLICANT},
            )

    def get_jobs(
        self,
        state: Optional[str] = None,
        department_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get job positions."""
        self._ensure_recruitment_module()

        domain = []
        # Note: 'state' field doesn't exist in Odoo 18 hr.job model
        # Filter by is_published or active instead if needed
        if department_id:
            domain.append(("department_id", "=", department_id))

        # Note: is_published requires website_hr_recruitment module, use active instead
        jobs = self.client.search_read(
            ODOO_MODEL_JOB,
            domain,
            fields=[
                "id", "name", "department_id", "description",
                "requirements", "no_of_recruitment", "no_of_hired_employee",
                "active"
            ],
        )

        return [
            {
                "id": job["id"],
                "name": job["name"],
                "department_id": job["department_id"][0] if job.get("department_id") else None,
                "department_name": job["department_id"][1] if job.get("department_id") else None,
                "description": job.get("description"),
                "requirements": job.get("requirements"),
                "no_of_recruitment": job.get("no_of_recruitment", 0),
                "no_of_hired_employee": job.get("no_of_hired_employee", 0),
                "state": "open" if job.get("active", True) else "closed",
            }
            for job in jobs
        ]

    def get_job_by_id(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific job by ID."""
        self._ensure_recruitment_module()

        jobs = self.client.search_read(
            ODOO_MODEL_JOB,
            [("id", "=", job_id)],
            fields=[
                "id", "name", "department_id", "description",
                "requirements", "no_of_recruitment", "no_of_hired_employee",
                "active"
            ],
        )

        if not jobs:
            return None

        job = jobs[0]
        return {
            "id": job["id"],
            "name": job["name"],
            "department_id": job["department_id"][0] if job.get("department_id") else None,
            "department_name": job["department_id"][1] if job.get("department_id") else None,
            "description": job.get("description"),
            "requirements": job.get("requirements"),
            "no_of_recruitment": job.get("no_of_recruitment", 0),
            "no_of_hired_employee": job.get("no_of_hired_employee", 0),
            "state": "open" if job.get("active", True) else "closed",
        }

    def get_applicants(
        self,
        filters: Any,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Get applicants with filters and pagination."""
        self._ensure_recruitment_module()

        domain = []
        if filters.job_id:
            domain.append(("job_id", "=", filters.job_id))
        if filters.stage_id:
            domain.append(("stage_id", "=", filters.stage_id))
        if filters.search:
            domain.append("|")
            domain.append(("partner_name", "ilike", filters.search))
            domain.append(("email_from", "ilike", filters.search))

        total = self.client.search_count(ODOO_MODEL_APPLICANT, domain)

        applicants = self.client.search_read(
            ODOO_MODEL_APPLICANT,
            domain,
            fields=[
                "id", "partner_name", "email_from", "partner_phone", "job_id",
                "stage_id", "priority", "create_date"
            ],
            limit=page_size,
            offset=(page - 1) * page_size,
            order="create_date desc",
        )

        items = [
            {
                "id": app["id"],
                "name": app.get("partner_name", "Unknown"),
                "email": app.get("email_from"),
                "phone": app.get("partner_phone"),
                "job_id": app["job_id"][0] if app.get("job_id") else None,
                "job_name": app["job_id"][1] if app.get("job_id") else None,
                "stage_id": app["stage_id"][0] if app.get("stage_id") else None,
                "stage_name": app["stage_id"][1] if app.get("stage_id") else None,
                "priority": app.get("priority", "0"),
                "create_date": app.get("create_date"),
                "cv_attached": False,  # Check attachment separately if needed
            }
            for app in applicants
        ]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    def get_applicant_by_id(self, applicant_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed applicant info."""
        self._ensure_recruitment_module()

        applicants = self.client.search_read(
            ODOO_MODEL_APPLICANT,
            [("id", "=", applicant_id)],
            fields=[
                "id", "partner_name", "email_from", "partner_phone", "job_id",
                "stage_id", "priority", "create_date", "applicant_notes"
            ],
        )

        if not applicants:
            return None

        app = applicants[0]

        # Get CV attachment if any
        attachments = self.client.search_read(
            ODOO_MODEL_ATTACHMENT,
            [("res_model", "=", ODOO_MODEL_APPLICANT), ("res_id", "=", applicant_id)],
            fields=["id", "name", "datas"],
            limit=1,
        )

        cv_text = None
        if attachments:
            # Decode and extract text if needed
            pass

        return {
            "id": app["id"],
            "name": app.get("partner_name", "Unknown"),
            "email": app.get("email_from"),
            "phone": app.get("partner_phone"),
            "job_id": app["job_id"][0] if app.get("job_id") else None,
            "job_name": app["job_id"][1] if app.get("job_id") else None,
            "stage_id": app["stage_id"][0] if app.get("stage_id") else None,
            "stage_name": app["stage_id"][1] if app.get("stage_id") else None,
            "priority": app.get("priority", "0"),
            "create_date": app.get("create_date"),
            "cv_attached": len(attachments) > 0,
            "cv_text": cv_text,
            "applicant_notes": app.get("applicant_notes"),
        }

    def _get_or_create_candidate(
        self, name: str, email: str, phone: Optional[str] = None
    ) -> int:
        """Get existing candidate by email or create a new one (Odoo 18 requirement)."""
        # Check if candidate exists with this email
        existing = self.client.search_read(
            ODOO_MODEL_CANDIDATE,
            [("email_from", "=", email)],
            fields=["id"],
            limit=1,
        )
        if existing:
            return existing[0]["id"]

        # Create new candidate
        candidate_values = {
            "partner_name": name,
            "email_from": email,
        }
        if phone:
            candidate_values["partner_phone"] = phone

        return self.client.create(ODOO_MODEL_CANDIDATE, candidate_values)

    def create_applicant(
        self,
        job_id: int,
        name: str,
        email: str,
        phone: Optional[str] = None,
        cv_content: bytes = None,
        cv_filename: str = None,
        cv_text: str = None,
    ) -> Dict[str, Any]:
        """Create a new applicant with optional CV."""
        self._ensure_recruitment_module()

        # Odoo 18: First create or get the candidate
        candidate_id = self._get_or_create_candidate(name, email, phone)

        # Create applicant linked to candidate
        values = {
            "candidate_id": candidate_id,
            "job_id": job_id,
        }

        if cv_text:
            values["applicant_notes"] = cv_text[:5000]  # Store first 5000 chars in applicant notes

        applicant_id = self.client.create(ODOO_MODEL_APPLICANT, values)

        # Attach CV if provided
        if cv_content and cv_filename:
            self.client.create(
                ODOO_MODEL_ATTACHMENT,
                {
                    "name": cv_filename,
                    "res_model": ODOO_MODEL_APPLICANT,
                    "res_id": applicant_id,
                    "datas": base64.b64encode(cv_content).decode("utf-8"),
                },
            )

        return {"id": applicant_id}

    def update_applicant_stage(self, applicant_id: int, stage_id: int) -> bool:
        """Update applicant's recruitment stage."""
        self._ensure_recruitment_module()

        # Verify applicant exists
        count = self.client.search_count(
            ODOO_MODEL_APPLICANT, [("id", "=", applicant_id)]
        )
        if count == 0:
            raise ApplicantNotFoundError(f"Applicant {applicant_id} not found")

        return self.client.write(
            ODOO_MODEL_APPLICANT, [applicant_id], {"stage_id": stage_id}
        )

    def update_applicant_analysis(
        self, applicant_id: int, analysis: Dict[str, Any]
    ) -> bool:
        """Store AI analysis results for an applicant."""
        self._ensure_recruitment_module()

        # Store as applicant_notes field (Odoo 18)
        summary = f"""
AI Analysis Score: {analysis.get('overall_score', 'N/A')}/100
Recommendation: {analysis.get('hiring_recommendation', 'N/A')}

Strengths: {', '.join(analysis.get('strengths', []))}
Concerns: {', '.join(analysis.get('concerns', []))}

Summary: {analysis.get('summary', '')}
"""
        return self.client.write(
            ODOO_MODEL_APPLICANT,
            [applicant_id],
            {"applicant_notes": summary},
        )

    async def rank_candidates_for_job(self, job_id: int) -> Dict[str, Any]:
        """Rank all candidates for a job using AI."""
        self._ensure_recruitment_module()

        job = self.get_job_by_id(job_id)
        if not job:
            raise JobNotFoundError(f"Job {job_id} not found")

        # Get all applicants for this job
        from app.models.applicant import ApplicantFilter
        result = self.get_applicants(
            ApplicantFilter(job_id=job_id),
            page=1,
            page_size=100,
        )

        applicants = result.get("items", [])
        if not applicants:
            return {
                "job_id": job_id,
                "job_name": job["name"],
                "rankings": [],
                "comparison_notes": "No applicants found for this job position.",
                "top_pick_rationale": "",
            }

        # Get detailed info for each applicant (including CV text)
        candidates_data = []
        for app in applicants:
            detail = self.get_applicant_by_id(app["id"])
            if detail:
                candidates_data.append({
                    "id": detail["id"],
                    "name": detail["name"],
                    "email": detail.get("email"),
                    "cv_text": detail.get("cv_text") or detail.get("applicant_notes") or "No CV/notes available",
                })

        # Build job description string
        job_description = f"""
Position: {job['name']}
Department: {job.get('department_name', 'Not specified')}
Requirements: {job.get('requirements', 'Not specified')}
Description: {job.get('description', 'Not specified')}
"""

        # Use Gemini AI to rank candidates
        from app.services.ai.gemini_client import get_gemini_client
        gemini = get_gemini_client()

        if not gemini.is_available():
            # Fallback: return basic list without AI ranking
            return {
                "job_id": job_id,
                "job_name": job["name"],
                "rankings": [
                    {
                        "rank": i + 1,
                        "applicant_id": c["id"],
                        "name": c["name"],
                        "overall_score": 0,
                        "recommendation": "AI unavailable - manual review required",
                    }
                    for i, c in enumerate(candidates_data)
                ],
                "comparison_notes": "AI service unavailable. Showing candidates in submission order.",
                "top_pick_rationale": "Manual review required.",
            }

        try:
            ai_result = await gemini.rank_candidates(
                job_description=job_description,
                candidates_data=candidates_data,
            )
            return {
                "job_id": job_id,
                "job_name": job["name"],
                "rankings": ai_result.get("rankings", []),
                "comparison_notes": ai_result.get("comparison_notes", ""),
                "top_pick_rationale": ai_result.get("top_pick_rationale", ""),
            }
        except Exception as e:
            logger.error(f"AI ranking failed: {e}")
            return {
                "job_id": job_id,
                "job_name": job["name"],
                "rankings": [],
                "comparison_notes": f"AI ranking failed: {str(e)}",
                "top_pick_rationale": "",
            }

    def get_interviews(
        self,
        applicant_id: Optional[int] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get scheduled interviews."""
        if not self.client.is_model_available(ODOO_MODEL_CALENDAR_EVENT):
            return []

        domain = [("res_model", "=", ODOO_MODEL_APPLICANT)]
        if applicant_id:
            domain.append(("res_id", "=", applicant_id))
        if from_date:
            domain.append(("start", ">=", from_date))
        if to_date:
            domain.append(("stop", "<=", to_date))

        events = self.client.search_read(
            ODOO_MODEL_CALENDAR_EVENT,
            domain,
            fields=["id", "name", "start", "stop", "partner_ids", "location", "description", "res_id"],
        )

        return [
            {
                "id": event["id"],
                "applicant_id": event.get("res_id"),
                "applicant_name": event.get("name", ""),
                "start_datetime": event.get("start"),
                "end_datetime": event.get("stop"),
                "interviewer_ids": event.get("partner_ids", []),
                "interviewer_names": [],  # Would need to resolve
                "location": event.get("location"),
                "notes": event.get("description"),
                "status": "scheduled",
            }
            for event in events
        ]

    def schedule_interview(
        self,
        applicant_id: int,
        start_datetime: datetime,
        duration_minutes: int,
        interviewer_ids: List[int],
        location: Optional[str] = None,
        notes: Optional[str] = None,
        send_notifications: bool = True,
    ) -> Dict[str, Any]:
        """Schedule a new interview."""
        self._ensure_recruitment_module()

        # Verify applicant exists
        applicant = self.get_applicant_by_id(applicant_id)
        if not applicant:
            raise ApplicantNotFoundError(f"Applicant {applicant_id} not found")

        end_datetime = start_datetime + timedelta(minutes=duration_minutes)

        event_values = {
            "name": f"Interview: {applicant['name']}",
            "start": start_datetime.isoformat(),
            "stop": end_datetime.isoformat(),
            "res_model": ODOO_MODEL_APPLICANT,
            "res_id": applicant_id,
            "partner_ids": [(6, 0, interviewer_ids)],
            "location": location,
            "description": notes,
        }

        event_id = self.client.create(ODOO_MODEL_CALENDAR_EVENT, event_values)

        return {
            "id": event_id,
            "applicant_id": applicant_id,
            "applicant_name": applicant["name"],
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "interviewer_ids": interviewer_ids,
            "interviewer_names": [],
            "location": location,
            "notes": notes,
            "status": "scheduled",
        }

    def cancel_interview(self, interview_id: int) -> bool:
        """Cancel an interview."""
        return self.client.unlink(ODOO_MODEL_CALENDAR_EVENT, [interview_id])


_service: Optional[RecruitmentService] = None


def get_recruitment_service() -> RecruitmentService:
    """Get the singleton recruitment service."""
    global _service
    if _service is None:
        _service = RecruitmentService()
    return _service
