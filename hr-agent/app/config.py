"""Application Configuration."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "hr-agent"
    APP_ENV: str = "development"
    DEBUG: bool = False
    API_KEY: str = ""
    PORT: int = 8002
    HOST: str = "0.0.0.0"

    # Odoo
    ODOO_URL: str = "http://localhost:8069"
    ODOO_DB: str = "odoo_db"
    ODOO_USER: str = "admin"
    ODOO_PASSWORD: str = ""

    # Redis (optional)
    REDIS_URL: str = "redis://localhost:6379/1"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 1

    # Gemini AI
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = ""

    # Webhooks
    WEBHOOK_SECRET: str = ""
    WEBHOOK_INTERVIEW_URL: str = ""
    WEBHOOK_APPRAISAL_URL: str = ""
    WEBHOOK_REPORT_URL: str = ""

    # HR Manager emails (comma-separated in env, parsed to list)
    HR_MANAGER_EMAILS: str = ""

    # Integration with other Ailigent services
    TASK_MANAGEMENT_URL: str = "http://localhost:8000"
    TASK_MANAGEMENT_API_KEY: str = ""

    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]

    # Scheduler
    SCHEDULER_TIMEZONE: str = "UTC"
    APPRAISAL_REMINDER_HOUR: int = 9
    INTERVIEW_REMINDER_HOURS: int = 4
    ATTENDANCE_CHECK_HOUR: int = 19
    WEEKLY_REPORT_DAY: str = "monday"
    WEEKLY_REPORT_HOUR: int = 7

    # Logging
    LOG_LEVEL: str = "INFO"

    # File Upload
    MAX_CV_SIZE_MB: int = 10
    ALLOWED_CV_EXTENSIONS: str = "pdf,docx"

    # Alert thresholds (days before expiry/deadline)
    APPRAISAL_REMINDER_DAYS: str = "7,3,1"
    INTERVIEW_REMINDER_HOURS_BEFORE: str = "48,24"

    @property
    def hr_manager_email_list(self) -> List[str]:
        """Parse comma-separated HR manager emails to list."""
        if not self.HR_MANAGER_EMAILS:
            return []
        return [email.strip() for email in self.HR_MANAGER_EMAILS.split(",") if email.strip()]

    @property
    def allowed_cv_extension_list(self) -> List[str]:
        """Parse comma-separated CV extensions to list."""
        return [ext.strip().lower() for ext in self.ALLOWED_CV_EXTENSIONS.split(",")]

    @property
    def appraisal_reminder_day_list(self) -> List[int]:
        """Parse comma-separated reminder days to list of integers."""
        return [int(d.strip()) for d in self.APPRAISAL_REMINDER_DAYS.split(",")]

    @property
    def interview_reminder_hour_list(self) -> List[int]:
        """Parse comma-separated interview reminder hours to list of integers."""
        return [int(h.strip()) for h in self.INTERVIEW_REMINDER_HOURS_BEFORE.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
