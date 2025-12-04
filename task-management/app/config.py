"""Application Configuration."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "task-management-agent"
    APP_ENV: str = "development"
    DEBUG: bool = False
    API_KEY: str = ""

    # Odoo
    ODOO_URL: str = "http://localhost:8069"
    ODOO_DB: str = "odoo_db"
    ODOO_USER: str = "admin"
    ODOO_PASSWORD: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

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
    WEBHOOK_OVERDUE_URL: str = ""
    WEBHOOK_ASSIGNMENT_URL: str = ""
    WEBHOOK_REPORT_URL: str = ""
    WEBHOOK_MANAGER_URL: str = ""

    # Manager emails (comma-separated in env, parsed to list)
    MANAGER_EMAILS: str = ""

    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]

    # Scheduler
    SCHEDULER_TIMEZONE: str = "UTC"

    # Logging
    LOG_LEVEL: str = "INFO"

    @property
    def manager_email_list(self) -> List[str]:
        """Parse comma-separated manager emails to list."""
        if not self.MANAGER_EMAILS:
            return []
        return [email.strip() for email in self.MANAGER_EMAILS.split(",") if email.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
