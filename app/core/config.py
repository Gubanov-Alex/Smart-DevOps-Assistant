"""Database configuration and settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseCompatibility:
    """Compatibility wrapper for database settings."""

    def __init__(self, settings_instance):
        self._settings = settings_instance

    @property
    def database_url(self):
        return self._settings.database_url

    @property
    def database_url_sync(self):
        return self._settings.database_url_sync

    @property
    def pool_size(self):
        return self._settings.pool_size

    @property
    def max_overflow(self):
        return self._settings.max_overflow

    @property
    def pool_timeout(self):
        return self._settings.pool_timeout

    @property
    def pool_recycle(self):
        return self._settings.pool_recycle

    @property
    def pool_pre_ping(self):
        return self._settings.pool_pre_ping

    @property
    def query_timeout(self):
        return self._settings.query_timeout

    @property
    def statement_timeout(self):
        return self._settings.statement_timeout

    @property
    def echo_sql(self):
        return self._settings.echo_sql

    @property
    def echo_pool(self):
        return self._settings.echo_pool


class Settings(BaseSettings):
    """Application settings."""

    # App configuration
    app_name: str = "Smart DevOps Assistant"
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Database settings
    database_url: str = Field(
        default="postgresql+asyncpg://devops_user:devops_pass@localhost:5433/devops_assistant",
        description="Async database URL for PostgreSQL",
    )
    database_url_sync: str = Field(
        default="postgresql://devops_user:devops_pass@localhost:5433/devops_assistant",
        description="Sync database URL for migrations",
    )

    # Redis settings for caching and events
    redis_url: str = Field(
        default="redis://localhost:6380/0", description="Redis connection URL"
    )

    # Security settings
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for JWT tokens",
    )

    # API settings
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="CORS allowed origins",
    )

    # Database pool settings
    pool_size: int = Field(default=10, description="Database connection pool size")
    max_overflow: int = Field(
        default=20, description="Max connections beyond pool size"
    )
    pool_timeout: int = Field(
        default=30, description="Pool checkout timeout in seconds"
    )
    pool_recycle: int = Field(
        default=3600, description="Connection recycle time in seconds"
    )
    pool_pre_ping: bool = Field(
        default=True, description="Validate connections before use"
    )

    # Query settings
    query_timeout: int = Field(default=30, description="Query timeout in seconds")
    statement_timeout: str = Field(
        default="30s", description="PostgreSQL statement timeout"
    )

    # Development settings
    echo_sql: bool = Field(default=False, description="Log all SQL statements")
    echo_pool: bool = Field(default=False, description="Log connection pool events")

    class Config:
        env_file = ".env"
        case_sensitive = False
        # Allow arbitrary attributes
        arbitrary_types_allowed = True
        extra = "allow"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set database compatibility after initialization
        object.__setattr__(self, "database", DatabaseCompatibility(self))


@lru_cache()
def get_settings() -> Settings:
    """Get application settings with caching."""
    return Settings()
