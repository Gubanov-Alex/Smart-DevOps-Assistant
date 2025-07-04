"""Repository dependencies and dependency injection setup with all repositories."""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.infrastructure.repositories.incident_repository import IncidentRepository
from app.infrastructure.repositories.log_repository import LogRepository
from app.infrastructure.repositories.mlmodel_repository import MLModelRepository


async def get_log_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AsyncGenerator[LogRepository, None]:
    """Dependency injection for LogRepository."""
    repository = LogRepository(session)
    try:
        yield repository
    finally:
        pass


async def get_incident_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AsyncGenerator[IncidentRepository, None]:
    """Dependency injection for IncidentRepository."""
    repository = IncidentRepository(session)
    try:
        yield repository
    finally:
        pass


async def get_mlmodel_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AsyncGenerator[MLModelRepository, None]:
    """Dependency injection for MLModelRepository."""
    repository = MLModelRepository(session)
    try:
        yield repository
    finally:
        pass


# Utility function for manual repository instantiation in tests
def create_repositories(
    session: AsyncSession,
) -> tuple[LogRepository, IncidentRepository, MLModelRepository]:
    """Create all repositories with given session for testing."""
    return (
        LogRepository(session),
        IncidentRepository(session),
        MLModelRepository(session),
    )
