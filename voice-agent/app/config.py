"""Voice Agent Configuration."""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8004

    # LiveKit Cloud
    LIVEKIT_URL: str = ""
    LIVEKIT_API_KEY: str = ""
    LIVEKIT_API_SECRET: str = ""

    # Google AI (Gemini)
    GOOGLE_API_KEY: str = ""

    # Odoo Configuration
    ODOO_URL: str = ""
    ODOO_DB: str = ""
    ODOO_USERNAME: str = ""
    ODOO_PASSWORD: str = ""

    # Backend Service URLs
    EMPLOYEE_AGENT_URL: str = "http://localhost:8000"
    TASK_MANAGEMENT_URL: str = "http://localhost:8003"
    CONTRACTS_AGENT_URL: str = "http://localhost:8001"
    HR_AGENT_URL: str = "http://localhost:8002"

    # Backend Service API Keys
    TASK_MANAGEMENT_API_KEY: str = "ailigent-task-api-key-2024"
    CONTRACTS_AGENT_API_KEY: str = "ailigent-contracts-api-key-2024"
    HR_AGENT_API_KEY: str = "ailigent-hr-api-key-2024"

    # Voice Settings
    DEFAULT_LANGUAGE: str = "en"  # "en" or "ar"
    VOICE_EN: str = "Puck"  # Gemini voice for English
    VOICE_AR: str = "Aoede"  # Voice for Arabic


settings = Settings()
