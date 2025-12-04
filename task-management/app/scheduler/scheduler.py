"""APScheduler Configuration and Management."""

import logging
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
import pytz

from app.config import settings

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Manages scheduled jobs for the Task Management Agent."""

    _instance: Optional["TaskScheduler"] = None

    def __new__(cls) -> "TaskScheduler":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Use memory job store (can be upgraded to Redis later)
        jobstores = {
            "default": MemoryJobStore(),
        }

        executors = {
            "default": ThreadPoolExecutor(10),
        }

        job_defaults = {
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 60,
        }

        timezone = pytz.timezone(settings.SCHEDULER_TIMEZONE)

        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=timezone,
        )

        self._initialized = True
        self._is_running = False

    def start(self):
        """Start scheduler and register all jobs."""
        if self._is_running:
            logger.warning("Scheduler already running")
            return

        self._register_jobs()
        self.scheduler.start()
        self._is_running = True
        logger.info("Task scheduler started")

    def shutdown(self):
        """Gracefully shutdown scheduler."""
        if not self._is_running:
            return

        self.scheduler.shutdown(wait=True)
        self._is_running = False
        logger.info("Task scheduler stopped")

    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._is_running

    def _register_jobs(self):
        """Register all scheduled jobs."""
        from app.scheduler.jobs.overdue_monitor import check_overdue_tasks
        from app.scheduler.jobs.report_generator import (
            generate_daily_report,
            generate_weekly_report,
        )
        from app.scheduler.jobs.workload_balancer import check_workload_balance

        # Overdue task monitoring - every 15 minutes
        self.scheduler.add_job(
            check_overdue_tasks,
            "interval",
            minutes=15,
            id="overdue_monitor",
            name="Overdue Task Monitor",
            replace_existing=True,
        )
        logger.info("Registered job: overdue_monitor (every 15 minutes)")

        # Daily report generation - 6:00 AM
        self.scheduler.add_job(
            generate_daily_report,
            "cron",
            hour=6,
            minute=0,
            id="daily_report",
            name="Daily Report Generator",
            replace_existing=True,
        )
        logger.info("Registered job: daily_report (6:00 AM)")

        # Weekly report generation - Monday 7:00 AM
        self.scheduler.add_job(
            generate_weekly_report,
            "cron",
            day_of_week="mon",
            hour=7,
            minute=0,
            id="weekly_report",
            name="Weekly Report Generator",
            replace_existing=True,
        )
        logger.info("Registered job: weekly_report (Monday 7:00 AM)")

        # Workload balance check - every hour
        self.scheduler.add_job(
            check_workload_balance,
            "interval",
            hours=1,
            id="workload_balance",
            name="Workload Balance Checker",
            replace_existing=True,
        )
        logger.info("Registered job: workload_balance (every hour)")

    def get_jobs(self) -> list:
        """Get list of all scheduled jobs."""
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time),
                "trigger": str(job.trigger),
            }
            for job in self.scheduler.get_jobs()
        ]

    def trigger_job(self, job_id: str) -> bool:
        """Manually trigger a job."""
        job = self.scheduler.get_job(job_id)
        if job:
            job.modify(next_run_time=None)
            self.scheduler.wakeup()
            logger.info(f"Manually triggered job: {job_id}")
            return True
        return False

    def pause_job(self, job_id: str) -> bool:
        """Pause a job."""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Paused job: {job_id}")
            return True
        except Exception:
            return False

    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job."""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Resumed job: {job_id}")
            return True
        except Exception:
            return False


_scheduler: Optional[TaskScheduler] = None


def get_scheduler() -> TaskScheduler:
    """Get the singleton scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler()
    return _scheduler
