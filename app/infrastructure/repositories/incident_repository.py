"""Production-ready IncidentRepository with advanced querying and transaction support."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog
from sqlalchemy import and_, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities import Incident as IncidentEntity
from app.domain.entities import IncidentSeverity, IncidentStatus
from app.infrastructure.mappers import IncidentMapper
from app.models import Incident as IncidentModel

logger = structlog.get_logger()


class RepositoryError(Exception):
    """Custom exception for repository operations."""

    pass


class IncidentRepository:
    """High-performance incident repository with advanced querying capabilities."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session
        self.mapper = IncidentMapper()

    async def save(self, incident: IncidentEntity) -> None:
        """Save an incident with full transaction support."""
        try:
            # Check if incident already exists
            existing = await self.session.get(IncidentModel, incident.id)

            if existing:
                # Update existing incident
                self.mapper.update_model_from_entity(existing, incident)
                existing.updated_at = datetime.now(timezone.utc)
            else:
                # Create new incident
                incident_model = self.mapper.to_model(incident)
                self.session.add(incident_model)

            await self.session.commit()
            logger.debug("Incident saved", incident_id=str(incident.id))

        except Exception as e:
            await self.session.rollback()
            logger.error(
                "Failed to save incident", error=str(e), incident_id=str(incident.id)
            )
            raise RepositoryError(f"Failed to save incident: {e}") from e

    async def find_by_id(self, incident_id: UUID) -> Optional[IncidentEntity]:
        """Find incident by ID with related logs."""
        try:
            stmt = (
                select(IncidentModel)
                .options(selectinload(IncidentModel.related_logs))
                .where(IncidentModel.id == incident_id)
            )

            result = await self.session.execute(stmt)
            incident_model = result.scalar_one_or_none()

            if incident_model:
                return self.mapper.to_entity(incident_model)
            return None

        except Exception as e:
            logger.error(
                "Failed to find incident by ID",
                error=str(e),
                incident_id=str(incident_id),
            )
            raise RepositoryError(f"Failed to find incident: {e}") from e

    async def find_open_incidents(self) -> List[IncidentEntity]:
        """Find all open incidents ordered by priority and creation date."""
        try:
            stmt = (
                select(IncidentModel)
                .where(
                    IncidentModel.status.in_(
                        [IncidentStatus.OPEN.value, IncidentStatus.IN_PROGRESS.value]
                    )
                )
                .order_by(
                    desc(IncidentModel.priority_score), desc(IncidentModel.created_at)
                )
            )

            result = await self.session.execute(stmt)
            incident_models = result.scalars().all()

            return [self.mapper.to_entity(model) for model in incident_models]

        except Exception as e:
            logger.error("Failed to find open incidents", error=str(e))
            raise RepositoryError(f"Failed to find open incidents: {e}") from e

    async def find_by_severity(
        self, severity: IncidentSeverity
    ) -> List[IncidentEntity]:
        """Find incidents by severity level with performance optimization."""
        try:
            stmt = (
                select(IncidentModel)
                .where(IncidentModel.severity == severity.value)
                .order_by(desc(IncidentModel.created_at))
                .limit(1000)  # Prevent unbounded queries
            )

            result = await self.session.execute(stmt)
            incident_models = result.scalars().all()

            return [self.mapper.to_entity(model) for model in incident_models]

        except Exception as e:
            logger.error(
                "Failed to find incidents by severity", error=str(e), severity=severity
            )
            raise RepositoryError(f"Failed to find incidents by severity: {e}") from e

    async def find_critical_incidents(
        self, since_hours: int = 24
    ) -> List[IncidentEntity]:
        """Find critical incidents within specified time period."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=since_hours)

            stmt = (
                select(IncidentModel)
                .where(
                    and_(
                        IncidentModel.severity == IncidentSeverity.CRITICAL.value,
                        IncidentModel.created_at >= cutoff_time,
                        IncidentModel.status.in_(
                            [
                                IncidentStatus.OPEN.value,
                                IncidentStatus.IN_PROGRESS.value,
                            ]
                        ),
                    )
                )
                .order_by(desc(IncidentModel.priority_score))
            )

            result = await self.session.execute(stmt)
            incident_models = result.scalars().all()

            return [self.mapper.to_entity(model) for model in incident_models]

        except Exception as e:
            logger.error("Failed to find critical incidents", error=str(e))
            raise RepositoryError(f"Failed to find critical incidents: {e}") from e

    async def update_status(self, incident_id: UUID, status: IncidentStatus) -> bool:
        """Update incident status with optimized single query."""
        try:
            update_data = {
                "status": status.value,
                "updated_at": datetime.now(timezone.utc),
            }

            # Set resolved_at for resolved status
            if status == IncidentStatus.RESOLVED:
                update_data["resolved_at"] = datetime.now(timezone.utc)

            stmt = (
                update(IncidentModel)
                .where(IncidentModel.id == incident_id)
                .values(**update_data)
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            updated = result.rowcount > 0
            if updated:
                logger.info(
                    "Incident status updated",
                    incident_id=str(incident_id),
                    status=status.value,
                )

            return updated

        except Exception as e:
            await self.session.rollback()
            logger.error(
                "Failed to update incident status",
                error=str(e),
                incident_id=str(incident_id),
            )
            raise RepositoryError(f"Failed to update incident status: {e}") from e

    async def find_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[IncidentEntity]:
        """Find incidents within time range with pagination."""
        try:
            stmt = (
                select(IncidentModel)
                .where(
                    and_(
                        IncidentModel.created_at >= start_time,
                        IncidentModel.created_at <= end_time,
                    )
                )
                .order_by(desc(IncidentModel.created_at))
                .limit(limit)
                .offset(offset)
            )

            result = await self.session.execute(stmt)
            incident_models = result.scalars().all()

            return [self.mapper.to_entity(model) for model in incident_models]

        except Exception as e:
            logger.error("Failed to find incidents by time range", error=str(e))
            raise RepositoryError(f"Failed to find incidents by time range: {e}") from e

    async def assign_incident(self, incident_id: UUID, assigned_to: str) -> bool:
        """Assign incident to team or person."""
        try:
            stmt = (
                update(IncidentModel)
                .where(IncidentModel.id == incident_id)
                .values(assigned_to=assigned_to, updated_at=datetime.now(timezone.utc))
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            updated = result.rowcount > 0
            if updated:
                logger.info(
                    "Incident assigned",
                    incident_id=str(incident_id),
                    assigned_to=assigned_to,
                )

            return updated

        except Exception as e:
            await self.session.rollback()
            logger.error(
                "Failed to assign incident", error=str(e), incident_id=str(incident_id)
            )
            raise RepositoryError(f"Failed to assign incident: {e}") from e

    async def get_incident_statistics(self, since_hours: int = 24) -> Dict[str, Any]:
        """Get incident statistics for monitoring dashboard."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=since_hours)

            # Count by status
            status_stmt = (
                select(
                    IncidentModel.status, func.count(IncidentModel.id).label("count")
                )
                .where(IncidentModel.created_at >= cutoff_time)
                .group_by(IncidentModel.status)
            )

            # Count by severity
            severity_stmt = (
                select(
                    IncidentModel.severity, func.count(IncidentModel.id).label("count")
                )
                .where(IncidentModel.created_at >= cutoff_time)
                .group_by(IncidentModel.severity)
            )

            # Average resolution time
            resolution_stmt = select(
                func.avg(IncidentModel.resolution_time_minutes).label(
                    "avg_resolution_time"
                )
            ).where(
                and_(
                    IncidentModel.created_at >= cutoff_time,
                    IncidentModel.status == IncidentStatus.RESOLVED.value,
                )
            )

            status_result = await self.session.execute(status_stmt)
            severity_result = await self.session.execute(severity_stmt)
            resolution_result = await self.session.execute(resolution_stmt)

            status_counts = {row.status: row.count for row in status_result}
            severity_counts = {row.severity: row.count for row in severity_result}
            avg_resolution = resolution_result.scalar() or 0

            return {
                "total_incidents": sum(status_counts.values()),
                "by_status": status_counts,
                "by_severity": severity_counts,
                "average_resolution_time_minutes": float(avg_resolution),
                "since_hours": since_hours,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error("Failed to get incident statistics", error=str(e))
            raise RepositoryError(f"Failed to get incident statistics: {e}") from e

    async def bulk_update_status(
        self, incident_ids: List[UUID], status: IncidentStatus
    ) -> int:
        """Bulk update status for multiple incidents."""
        try:
            update_data = {
                "status": status.value,
                "updated_at": datetime.now(timezone.utc),
            }

            if status == IncidentStatus.RESOLVED:
                update_data["resolved_at"] = datetime.now(timezone.utc)

            stmt = (
                update(IncidentModel)
                .where(IncidentModel.id.in_(incident_ids))
                .values(**update_data)
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            updated_count = result.rowcount
            logger.info(
                "Bulk status update completed",
                updated_count=updated_count,
                status=status.value,
            )

            return updated_count

        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to bulk update incident status", error=str(e))
            raise RepositoryError(f"Failed to bulk update incident status: {e}") from e
