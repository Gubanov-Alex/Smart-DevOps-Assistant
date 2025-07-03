"""Production-ready LogRepository implementation with batch operations and optimization."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog
from sqlalchemy import and_, desc, func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import LogEntry as LogEntryEntity
from app.domain.entities import LogLevel
from app.infrastructure.mappers import LogEntryMapper
from app.models import LogEntry as LogEntryModel

logger = structlog.get_logger()


class RepositoryError(Exception):
    """Custom exception for repository operations."""

    pass


class LogRepository:
    """High-performance log repository with batch operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session
        self.mapper = LogEntryMapper()
        self._batch_size = 1000

    async def save(self, log: LogEntryEntity) -> None:
        """Save a single log entry."""
        try:
            log_model = self.mapper.to_model(log)
            self.session.add(log_model)
            await self.session.commit()

            logger.debug("Log entry saved", log_id=str(log.id))

        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to save log entry", error=str(e))
            raise RepositoryError(f"Failed to save log entry: {e}") from e

    async def save_batch(self, logs: List[LogEntryEntity]) -> None:
        """Save multiple log entries in optimized batch operation."""
        if not logs:
            return

        try:
            # Process logs in chunks
            for i in range(0, len(logs), self._batch_size):
                chunk = logs[i : i + self._batch_size]

                # Convert to model data for bulk insert
                log_data = []
                for log in chunk:
                    model_data = {
                        "id": log.id,
                        "message": log.message,
                        "level": log.level.value.upper(),
                        "source": log.source,
                        "timestamp": log.timestamp,
                        "extra_data": log.metadata,
                        "created_at": datetime.utcnow(),
                    }
                    log_data.append(model_data)

                # Use PostgreSQL bulk insert with conflict resolution
                stmt = insert(LogEntryModel).values(log_data)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["id"],
                    set_=dict(
                        message=stmt.excluded.message,
                        level=stmt.excluded.level,
                        extra_data=stmt.excluded.extra_data,
                    ),
                )

                await self.session.execute(stmt)

            await self.session.commit()
            logger.info("Batch log save completed", total_logs=len(logs))

        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to save log batch", error=str(e))
            raise RepositoryError(f"Failed to save log batch: {e}") from e

    async def find_by_id(self, log_id: UUID) -> Optional[LogEntryEntity]:
        """Find log entry by ID."""
        try:
            result = await self.session.get(LogEntryModel, log_id)
            return self.mapper.to_entity(result) if result else None
        except Exception as e:
            logger.error("Failed to find log by ID", error=str(e))
            raise RepositoryError(f"Failed to find log by ID: {e}") from e

    async def find_by_source(
        self, source: str, limit: int = 100
    ) -> List[LogEntryEntity]:
        """Find log entries by source system."""
        try:
            stmt = (
                select(LogEntryModel)
                .where(LogEntryModel.source == source)
                .order_by(desc(LogEntryModel.timestamp))
                .limit(limit)
            )

            result = await self.session.execute(stmt)
            models = result.scalars().all()

            return [self.mapper.to_entity(model) for model in models]

        except Exception as e:
            logger.error("Failed to find logs by source", error=str(e))
            raise RepositoryError(f"Failed to find logs by source: {e}") from e

    async def find_critical_logs(self, since_minutes: int = 60) -> List[LogEntryEntity]:
        """Find critical logs within time period."""
        return await self.find_by_levels(
            levels=[LogLevel.ERROR, LogLevel.CRITICAL],
            since_minutes=since_minutes,
            limit=1000,
        )

    async def find_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[LogEntryEntity]:
        """Find logs within specific time range with pagination."""
        try:
            stmt = (
                select(LogEntryModel)
                .where(
                    and_(
                        LogEntryModel.timestamp >= start_time,
                        LogEntryModel.timestamp <= end_time,
                    )
                )
                .order_by(desc(LogEntryModel.timestamp))
                .limit(limit)
                .offset(offset)
            )

            result = await self.session.execute(stmt)
            models = result.scalars().all()

            return [self.mapper.to_entity(model) for model in models]

        except Exception as e:
            logger.error("Failed to find logs by time range", error=str(e))
            raise RepositoryError(f"Failed to find logs by time range: {e}") from e

    async def find_by_level(
        self, level: LogLevel, since_minutes: int = 60, limit: int = 1000
    ) -> List[LogEntryEntity]:
        """Find logs by specific level within time period."""
        return await self.find_by_levels([level], since_minutes, limit)

    async def find_by_levels(
        self, levels: List[LogLevel], since_minutes: int = 60, limit: int = 1000
    ) -> List[LogEntryEntity]:
        """Find logs by multiple levels."""
        try:
            since_time = datetime.utcnow() - timedelta(minutes=since_minutes)
            level_values = [level.value.upper() for level in levels]

            stmt = (
                select(LogEntryModel)
                .where(
                    and_(
                        LogEntryModel.level.in_(level_values),
                        LogEntryModel.timestamp >= since_time,
                    )
                )
                .order_by(desc(LogEntryModel.timestamp))
                .limit(limit)
            )

            result = await self.session.execute(stmt)
            models = result.scalars().all()

            return [self.mapper.to_entity(model) for model in models]

        except Exception as e:
            logger.error("Failed to find logs by levels", error=str(e))
            raise RepositoryError(f"Failed to find logs by levels: {e}") from e

    async def count_by_level_and_time(
        self, level: LogLevel, since_minutes: int = 60
    ) -> int:
        """Count logs by level within time period."""
        try:
            since_time = datetime.utcnow() - timedelta(minutes=since_minutes)

            stmt = select(func.count(LogEntryModel.id)).where(
                and_(
                    LogEntryModel.level == level.value.upper(),
                    LogEntryModel.timestamp >= since_time,
                )
            )

            result = await self.session.execute(stmt)
            count = result.scalar() or 0

            return count

        except Exception as e:
            logger.error("Failed to count logs by level", error=str(e))
            raise RepositoryError(f"Failed to count logs by level: {e}") from e

    async def get_log_statistics(self, since_minutes: int = 60) -> Dict[str, Any]:
        """Get aggregated log statistics for monitoring dashboard."""
        try:
            since_time = datetime.utcnow() - timedelta(minutes=since_minutes)

            # Level distribution query
            level_stats_stmt = (
                select(LogEntryModel.level, func.count(LogEntryModel.id).label("count"))
                .where(LogEntryModel.timestamp >= since_time)
                .group_by(LogEntryModel.level)
            )

            # Total count query
            total_count_stmt = select(func.count(LogEntryModel.id)).where(
                LogEntryModel.timestamp >= since_time
            )

            # Execute queries
            level_result = await self.session.execute(level_stats_stmt)
            total_result = await self.session.execute(total_count_stmt)

            # Process results
            level_distribution = {
                row.level: row.count for row in level_result.fetchall()
            }

            total_count = total_result.scalar() or 0

            statistics = {
                "total_logs": total_count,
                "time_window_minutes": since_minutes,
                "level_distribution": level_distribution,
                "critical_logs": level_distribution.get("CRITICAL", 0),
                "error_logs": level_distribution.get("ERROR", 0),
                "error_rate": (
                    (
                        level_distribution.get("ERROR", 0)
                        + level_distribution.get("CRITICAL", 0)
                    )
                    / max(total_count, 1)
                ),
                "generated_at": datetime.utcnow().isoformat(),
            }

            return statistics

        except Exception as e:
            logger.error("Failed to get log statistics", error=str(e))
            raise RepositoryError(f"Failed to get log statistics: {e}") from e

    async def find_logs_with_anomalies(
        self, threshold: float = 0.7, limit: int = 100
    ) -> List[LogEntryEntity]:
        """Find logs with anomaly scores above threshold."""
        try:
            stmt = (
                select(LogEntryModel)
                .where(
                    and_(
                        LogEntryModel.anomaly_score.is_not(None),
                        LogEntryModel.anomaly_score >= threshold,
                    )
                )
                .order_by(desc(LogEntryModel.anomaly_score))
                .limit(limit)
            )

            result = await self.session.execute(stmt)
            models = result.scalars().all()

            return [self.mapper.to_entity(model) for model in models]

        except Exception as e:
            logger.error("Failed to find logs with anomalies", error=str(e))
            raise RepositoryError(f"Failed to find logs with anomalies: {e}") from e

    async def delete_old_logs(self, older_than_days: int = 30) -> int:
        """Delete logs older than specified days."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=older_than_days)

            delete_stmt = text(
                """
                DELETE FROM log_entries
                WHERE timestamp < :cutoff_time
            """
            )

            result = await self.session.execute(
                delete_stmt, {"cutoff_time": cutoff_time}
            )

            deleted_count = result.rowcount
            await self.session.commit()

            logger.info("Old logs deleted", deleted_count=deleted_count)
            return deleted_count

        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to delete old logs", error=str(e))
            raise RepositoryError(f"Failed to delete old logs: {e}") from e
