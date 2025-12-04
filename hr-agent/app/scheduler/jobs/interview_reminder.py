"""Interview Reminder Job."""

import logging
from datetime import datetime, timedelta

from app.config import settings

logger = logging.getLogger(__name__)


async def run_interview_reminders():
    """Send reminders for upcoming interviews."""
    logger.info("Running interview reminder job...")

    try:
        from app.services.odoo.recruitment_service import get_recruitment_service

        service = get_recruitment_service()

        # Get reminder hours from settings
        reminder_hours = settings.interview_reminder_hour_list

        for hours in reminder_hours:
            from_time = datetime.now()
            to_time = from_time + timedelta(hours=hours)

            interviews = service.get_interviews(
                from_date=from_time.isoformat(),
                to_date=to_time.isoformat(),
            )

            if interviews:
                logger.info(f"Found {len(interviews)} interviews in next {hours} hours")

                # Send reminders (placeholder - would integrate with notification service)
                for interview in interviews:
                    logger.info(
                        f"Reminder: Interview for {interview.get('applicant_name')} "
                        f"at {interview.get('start_datetime')}"
                    )

        logger.info("Interview reminder job completed")

    except Exception as e:
        logger.error(f"Interview reminder job failed: {e}")
