"""Application configuration management with Pydantic v2."""
from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Environment
    environment: Literal["development", "testing", "production"] = "development"
    debug: bool = Field(default=False, description="Enable debug mode")

    # API Settings
    api_title: str = "Smart DevOps Assistant"
    api_version: str = "0.1.0"
    api_description: str = "AI-powered DevOps assistant for log analysis and anomaly detection"

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://devops_user:devops_pass@localhost:5432/devops_assistant",
        description="PostgreSQL database URL",
    )
    database_echo: bool = Field(default=False, description="Echo SQL queries")

    # Redis
    redis_url: RedisDsn = Field(
        default="redis://localhost:6379/0", description="Redis URL for caching"
    )

    # Celery
    celery_broker_url: RedisDsn = Field(
        default="redis://localhost:6379/1", description="Celery broker URL"
    )
    celery_result_backend: RedisDsn = Field(
        default="redis://localhost:6379/1", description="Celery result backend URL"
    )

    # Security
    secret_key: str = Field(
        default="super-secret-key-change-in-production", description="Secret key for JWT tokens"
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # ML Models
    model_path: str = Field(default="./models", description="Path to ML models")
    batch_size: int = Field(default=32, description="Batch size for ML inference")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = "json"

    # Health Check
    health_check_timeout: int = Field(default=30, description="Health check timeout in seconds")

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"

    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.environment == "testing"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
