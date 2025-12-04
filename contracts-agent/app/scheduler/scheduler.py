"""APScheduler Configuration and Management."""

import logging
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
import pytz

from app.config import settings

logger = logging.getLogger(__name__)


class ContractScheduler:
    """Manages scheduled jobs for the Contracts Agent."""

    _instance: Optional["ContractScheduler"] = None

    def __new__(cls) -> "ContractScheduler":
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
        logger.info("Contract scheduler started")

    def shutdown(self):
        """Gracefully shutdown scheduler."""
        if not self._is_running:
            return

        self.scheduler.shutdown(wait=True)
        self._is_running = False
        logger.info("Contract scheduler stopped")

    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._is_running

    def _register_jobs(self):
        """Register all scheduled jobs."""
        from app.scheduler.jobs.expiry_monitor import check_contract_expiry
        from app.scheduler.jobs.delivery_monitor import check_delivery_dates
        from app.scheduler.jobs.compliance_checker import check_compliance_status

        # Contract expiry monitoring - Daily at 7:00 AM
        self.scheduler.add_job(
            check_contract_expiry,
            "cron",
            hour=7,
            minute=0,
            id="expiry_monitor",
            name="Contract Expiry Monitor",
            replace_existing=True,
        )
        logger.info("Registered job: expiry_monitor (daily 7:00 AM)")

        # Delivery date monitoring - Every 6 hours
        self.scheduler.add_job(
            check_delivery_dates,
            "interval",
            hours=6,
            id="delivery_monitor",
            name="Delivery Date Monitor",
            replace_existing=True,
        )
        logger.info("Registered job: delivery_monitor (every 6 hours)")

        # Compliance status check - Weekly Monday 8:00 AM
        self.scheduler.add_job(
            check_compliance_status,
            "cron",
            day_of_week="mon",
            hour=8,
            minute=0,
            id="compliance_checker",
            name="Compliance Status Checker",
            replace_existing=True,
        )
        logger.info("Registered job: compliance_checker (Monday 8:00 AM)")

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


_scheduler: Optional[ContractScheduler] = None


def get_scheduler() -> ContractScheduler:
    """Get the singleton scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = ContractScheduler()
    return _scheduler
