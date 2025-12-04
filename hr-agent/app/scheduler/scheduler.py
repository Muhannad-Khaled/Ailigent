"""APScheduler Configuration for HR Agent."""

import logging
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings

logger = logging.getLogger(__name__)

_scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    """Get or create the scheduler instance."""
    global _scheduler

    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone=settings.SCHEDULER_TIMEZONE)
        _register_jobs(_scheduler)

    return _scheduler


def _register_jobs(scheduler: AsyncIOScheduler) -> None:
    """Register all scheduled jobs."""

    # Appraisal Reminders - Daily at configured hour
    scheduler.add_job(
        "app.scheduler.jobs.appraisal_reminder:run_appraisal_reminders",
        CronTrigger(hour=settings.APPRAISAL_REMINDER_HOUR, minute=0),
        id="appraisal_reminders",
        name="Send appraisal reminders",
        replace_existing=True,
    )
    logger.info(f"Registered: appraisal_reminders (daily at {settings.APPRAISAL_REMINDER_HOUR}:00)")

    # Interview Reminders - Every N hours
    scheduler.add_job(
        "app.scheduler.jobs.interview_reminder:run_interview_reminders",
        IntervalTrigger(hours=settings.INTERVIEW_REMINDER_HOURS),
        id="interview_reminders",
        name="Send interview reminders",
        replace_existing=True,
    )
    logger.info(f"Registered: interview_reminders (every {settings.INTERVIEW_REMINDER_HOURS} hours)")

    # Attendance Anomaly Detection - Daily at configured hour
    scheduler.add_job(
        "app.scheduler.jobs.attendance_anomaly:run_attendance_check",
        CronTrigger(hour=settings.ATTENDANCE_CHECK_HOUR, minute=0),
        id="attendance_anomaly",
        name="Check attendance anomalies",
        replace_existing=True,
    )
    logger.info(f"Registered: attendance_anomaly (daily at {settings.ATTENDANCE_CHECK_HOUR}:00)")

    # Weekly HR Report - Configured day and hour
    day_mapping = {
        "monday": "mon",
        "tuesday": "tue",
        "wednesday": "wed",
        "thursday": "thu",
        "friday": "fri",
        "saturday": "sat",
        "sunday": "sun",
    }
    day = day_mapping.get(settings.WEEKLY_REPORT_DAY.lower(), "mon")

    scheduler.add_job(
        "app.scheduler.jobs.report_scheduler:run_weekly_report",
        CronTrigger(day_of_week=day, hour=settings.WEEKLY_REPORT_HOUR, minute=0),
        id="weekly_hr_report",
        name="Generate weekly HR report",
        replace_existing=True,
    )
    logger.info(f"Registered: weekly_hr_report ({settings.WEEKLY_REPORT_DAY} at {settings.WEEKLY_REPORT_HOUR}:00)")
