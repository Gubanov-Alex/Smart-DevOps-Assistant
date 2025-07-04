"""Database session management with async support and connection pooling.

This module provides optimized database session management for high-throughput
log ingestion and ML model operations using SQLAlchemy async engine.
"""

import asyncio
import contextlib
from typing import AsyncGenerator, Optional

import structlog
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.models import Base

logger = structlog.get_logger()


class DatabaseManager:
    """Database connection and session manager with async support.

    Provides optimized connection pooling, session management, and
    health monitoring for production database operations.
    """

    def __init__(self) -> None:
        """Initialize database manager."""
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self._is_initialized = False

    async def initialize(self) -> None:
        """Initialize database engine and session factory.

        Creates async engine with optimized connection pool settings
        for high-throughput operations.
        """
        if self._is_initialized:
            logger.info("Database already initialized")
            return

        settings = get_settings()

        logger.info(
            "Initializing database connection",
            database_url=(
                settings.database.database_url.split("@")[1]
                if "@" in settings.database.database_url
                else "unknown"
            ),
        )

        # Create async engine with connection pooling
        self._engine = create_async_engine(
            settings.database.database_url,
            # Connection pool configuration
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            pool_timeout=settings.database.pool_timeout,
            pool_recycle=settings.database.pool_recycle,
            pool_pre_ping=settings.database.pool_pre_ping,
            # Query configuration
            query_cache_size=1200,
            # Connection arguments for PostgreSQL optimization
            connect_args={
                "server_settings": {
                    "application_name": "smart_devops_assistant",
                    "statement_timeout": str(settings.database.statement_timeout),
                },
                "command_timeout": settings.database.query_timeout,
            },
            # Logging configuration
            echo=settings.database.echo_sql,
            echo_pool=settings.database.echo_pool,
            # Performance optimizations
            future=True,
        )

        # Create session factory
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False,
        )

        # Add connection pool event listeners for monitoring
        self._setup_pool_events()

        # Test connection
        await self._test_connection()

        self._is_initialized = True
        logger.info("Database initialization completed successfully")

    async def close(self) -> None:
        """Close database connections and cleanup resources."""
        if not self._is_initialized:
            return

        if self._engine:
            logger.info("Closing database connections")
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

        self._is_initialized = False
        logger.info("Database connections closed")

    @contextlib.asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with automatic cleanup.

        Usage:
            async with db_manager.get_session() as session:
                result = await session.execute(query)
                await session.commit()

        Yields:
            AsyncSession: Database session with automatic transaction management
        """
        if not self._is_initialized:
            await self.initialize()

        if not self._session_factory:
            raise RuntimeError("Database not initialized")

        session = self._session_factory()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def create_tables(self) -> None:
        """Create all database tables.

        Used for initial database setup and testing.
        """
        if not self._engine:
            await self.initialize()

        logger.info("Creating database tables")
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")

    async def drop_tables(self) -> None:
        """Drop all database tables.

        WARNING: This will delete all data. Use only for testing.
        """
        if not self._engine:
            await self.initialize()

        logger.warning("Dropping all database tables")
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.warning("All database tables dropped")

    async def health_check(self) -> bool:
        """Check database connection health.

        Returns:
            bool: True if database is healthy, False otherwise
        """
        try:
            # Use simple connection check without get_session to avoid recursion
            if not self._engine:
                return False

            async with self._engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
                return True
        except Exception as exc:
            logger.error("Database health check failed", error=str(exc))
            return False

    def get_pool_status(self) -> dict:
        """Get connection pool status for monitoring.

        Returns:
            dict: Pool status information
        """
        if not self._engine or not self._engine.pool:
            return {"status": "not_initialized"}

        pool = self._engine.pool
        return {
            "status": "active",
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
        }

    async def _test_connection(self) -> None:
        """Test database connection during initialization."""
        try:
            if not self._engine:
                raise RuntimeError("Engine not initialized")

            async with self._engine.begin() as conn:
                await conn.execute(text("SELECT version()"))
            logger.info("Database connection test successful")
        except Exception as exc:
            logger.error("Database connection test failed", error=str(exc))
            raise

    def _setup_pool_events(self) -> None:
        """Setup connection pool event listeners for monitoring."""
        if not self._engine:
            return

        @event.listens_for(self._engine.sync_engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            """Log new database connections."""
            logger.debug("New database connection established")

        @event.listens_for(self._engine.sync_engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Log connection checkout from pool."""
            logger.debug("Database connection checked out from pool")

        @event.listens_for(self._engine.sync_engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Log connection checkin to pool."""
            logger.debug("Database connection returned to pool")


# Global database manager instance
db_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency function for FastAPI to inject database sessions.

    Usage in FastAPI endpoints:
        @app.get("/logs")
        async def get_logs(db: AsyncSession = Depends(get_db_session)):
            # Use db session

    Yields:
        AsyncSession: Database session
    """
    async with db_manager.get_session() as session:
        yield session


async def init_database() -> None:
    """Initialize database for application startup."""
    await db_manager.initialize()


async def close_database() -> None:
    """Close database connections for application shutdown."""
    await db_manager.close()


# Database session context manager for manual usage
@contextlib.asynccontextmanager
async def database_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions.

    Usage:
        async with database_session() as session:
            logs = await session.execute(select(LogEntry))
    """
    async with db_manager.get_session() as session:
        yield session


# Utility functions for common database operations
async def execute_with_retry(
    session: AsyncSession, query, max_retries: int = 3, retry_delay: float = 1.0
):
    """Execute query with automatic retry on transient failures.

    Args:
        session: Database session
        query: SQLAlchemy query to execute
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds

    Returns:
        Query result
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await session.execute(query)
        except Exception as exc:
            last_exception = exc
            if attempt < max_retries:
                logger.warning(
                    "Query execution failed, retrying",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    error=str(exc),
                )
                await asyncio.sleep(retry_delay * (2**attempt))  # Exponential backoff
            else:
                logger.error("Query execution failed after all retries", error=str(exc))

    raise last_exception


# Export commonly used components
__all__ = [
    "DatabaseManager",
    "db_manager",
    "get_db_session",
    "init_database",
    "close_database",
    "database_session",
    "execute_with_retry",
]
