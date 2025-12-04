"""Appraisal Reminder Job."""

import logging
from datetime import date, timedelta

from app.config import settings

logger = logging.getLogger(__name__)


async def run_appraisal_reminders():
    """Send reminders for pending appraisals."""
    logger.info("Running appraisal reminder job...")

    try:
        from app.services.odoo.appraisal_service import get_appraisal_service

        service = get_appraisal_service()

        # Get reminder days from settings
        reminder_days = settings.appraisal_reminder_day_list

        for days in reminder_days:
            pending = service.get_pending_appraisals(days_until_deadline=days)

            if pending:
                logger.info(f"Found {len(pending)} appraisals due within {days} days")

                # Send reminders
                result = service.send_reminders(days_until_deadline=days)
                logger.info(f"Sent {result.get('count', 0)} reminders")

        logger.info("Appraisal reminder job completed")

    except Exception as e:
        logger.error(f"Appraisal reminder job failed: {e}")
