"""Application configuration from environment variables."""

import json
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "contracts-agent"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_KEY: str = ""
    LOG_LEVEL: str = "INFO"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    # Odoo Connection
    ODOO_URL: str = "http://localhost:8069"
    ODOO_DB: str = "odoo_db"
    ODOO_USER: str = "admin"
    ODOO_PASSWORD: str = "admin"

    # Google Gemini AI
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Webhooks
    WEBHOOK_SECRET: str = ""
    WEBHOOK_BASE_URL: str = "http://localhost:8000/api/v1"
    WEBHOOK_CONTRACT_EXPIRY_URL: str = ""
    WEBHOOK_MILESTONE_URL: str = ""
    WEBHOOK_COMPLIANCE_URL: str = ""
    WEBHOOK_REPORT_URL: str = ""

    # Alert Thresholds
    EXPIRY_ALERT_DAYS: str = "30,14,7"
    MILESTONE_ALERT_DAYS: str = "7,3,1"

    # Scheduler
    SCHEDULER_TIMEZONE: str = "UTC"

    # CORS
    ALLOWED_ORIGINS: str = '["http://localhost:3000","http://localhost:8080"]'

    @property
    def expiry_alert_days_list(self) -> List[int]:
        """Parse expiry alert days as list of integers."""
        return [int(d.strip()) for d in self.EXPIRY_ALERT_DAYS.split(",")]

    @property
    def milestone_alert_days_list(self) -> List[int]:
        """Parse milestone alert days as list of integers."""
        return [int(d.strip()) for d in self.MILESTONE_ALERT_DAYS.split(",")]

    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse allowed origins as list."""
        try:
            return json.loads(self.ALLOWED_ORIGINS)
        except json.JSONDecodeError:
            return ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
