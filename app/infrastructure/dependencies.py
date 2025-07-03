"""Repository dependencies and dependency injection setup."""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.infrastructure.repositories.log_repository import LogRepository


async def get_log_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AsyncGenerator[LogRepository, None]:
    """Dependency injection for LogRepository."""
    repository = LogRepository(session)
    try:
        yield repository
    finally:
        pass
