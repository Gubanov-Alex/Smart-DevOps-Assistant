"""Production-ready MLModelRepository with versioning and lifecycle management."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog
from sqlalchemy import and_, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import MLModel as MLModelEntity
from app.domain.entities import ModelStatus
from app.infrastructure.mappers import MLModelMapper
from app.models import MLModel as MLModelModel

logger = structlog.get_logger()


class RepositoryError(Exception):
    """Custom exception for repository operations."""

    pass


class MLModelRepository:
    """High-performance ML model repository with versioning and lifecycle management."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session
        self.mapper = MLModelMapper()

    async def save(self, model: MLModelEntity) -> None:
        """Save ML model with conflict resolution and version management."""
        try:
            # Check if model with same name and version exists
            existing = await self.find_by_name_and_version(model.name, model.version)

            if existing:
                # Update existing model
                existing_model = await self.session.get(MLModelModel, existing.id)
                if existing_model:
                    self.mapper.update_model_from_entity(existing_model, model)
                    existing_model.updated_at = datetime.now(timezone.utc)
            else:
                # Create new model
                model_db = self.mapper.to_model(model)
                self.session.add(model_db)

            await self.session.commit()
            logger.debug(
                "ML model saved",
                model_id=str(model.id),
                name=model.name,
                version=model.version,
            )

        except Exception as e:
            await self.session.rollback()
            logger.error(
                "Failed to save ML model", error=str(e), model_id=str(model.id)
            )
            raise RepositoryError(f"Failed to save ML model: {e}") from e

    async def find_by_name_and_version(
        self, name: str, version: str
    ) -> Optional[MLModelEntity]:
        """Find model by exact name and version match."""
        try:
            stmt = select(MLModelModel).where(
                and_(MLModelModel.name == name, MLModelModel.version == version)
            )

            result = await self.session.execute(stmt)
            model_db = result.scalar_one_or_none()

            if model_db:
                return self.mapper.to_entity(model_db)
            return None

        except Exception as e:
            logger.error(
                "Failed to find model by name and version",
                error=str(e),
                name=name,
                version=version,
            )
            raise RepositoryError(f"Failed to find model: {e}") from e

    async def find_latest_ready(self, model_type: str) -> Optional[MLModelEntity]:
        """Find latest ready/deployed model of given type with performance metrics."""
        try:
            stmt = (
                select(MLModelModel)
                .where(
                    and_(
                        MLModelModel.model_type == model_type,
                        MLModelModel.status.in_(
                            [ModelStatus.TRAINED.value, ModelStatus.DEPLOYED.value]
                        ),
                        MLModelModel.is_active == True,
                    )
                )
                .order_by(
                    desc(MLModelModel.deployed_at),
                    desc(MLModelModel.trained_at),
                    desc(MLModelModel.created_at),
                )
                .limit(1)
            )

            result = await self.session.execute(stmt)
            model_db = result.scalar_one_or_none()

            if model_db:
                return self.mapper.to_entity(model_db)
            return None

        except Exception as e:
            logger.error(
                "Failed to find latest ready model", error=str(e), model_type=model_type
            )
            raise RepositoryError(f"Failed to find latest ready model: {e}") from e

    async def find_all_versions(self, name: str) -> List[MLModelEntity]:
        """Find all versions of a model ordered by version descending."""
        try:
            stmt = (
                select(MLModelModel)
                .where(MLModelModel.name == name)
                .order_by(desc(MLModelModel.created_at))
            )

            result = await self.session.execute(stmt)
            model_dbs = result.scalars().all()

            return [self.mapper.to_entity(model_db) for model_db in model_dbs]

        except Exception as e:
            logger.error("Failed to find all model versions", error=str(e), name=name)
            raise RepositoryError(f"Failed to find all model versions: {e}") from e

    async def get_by_id(self, model_id: UUID) -> Optional[MLModelEntity]:
        """Get model by ID with full details."""
        try:
            model_db = await self.session.get(MLModelModel, model_id)

            if model_db:
                return self.mapper.to_entity(model_db)
            return None

        except Exception as e:
            logger.error(
                "Failed to get model by ID", error=str(e), model_id=str(model_id)
            )
            raise RepositoryError(f"Failed to get model by ID: {e}") from e

    async def get_active_models(self) -> List[MLModelEntity]:
        """Get all active models with deployment status."""
        try:
            stmt = (
                select(MLModelModel)
                .where(
                    and_(
                        MLModelModel.is_active == True,
                        MLModelModel.status.in_(
                            [ModelStatus.TRAINED.value, ModelStatus.DEPLOYED.value]
                        ),
                    )
                )
                .order_by(MLModelModel.model_type, desc(MLModelModel.deployed_at))
            )

            result = await self.session.execute(stmt)
            model_dbs = result.scalars().all()

            return [self.mapper.to_entity(model_db) for model_db in model_dbs]

        except Exception as e:
            logger.error("Failed to get active models", error=str(e))
            raise RepositoryError(f"Failed to get active models: {e}") from e

    async def update_status(
        self,
        model_id: UUID,
        status: ModelStatus,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update model status with optional metadata."""
        try:
            update_data = {
                "status": status.value,
                "updated_at": datetime.now(timezone.utc),
            }

            # Set deployment timestamp for deployed status
            if status == ModelStatus.DEPLOYED:
                update_data["deployed_at"] = datetime.now(timezone.utc)

            # Update metadata if provided
            if metadata:
                # Get existing model to merge metadata
                existing = await self.session.get(MLModelModel, model_id)
                if existing and existing.extra_data:
                    merged_metadata = {**existing.extra_data, **metadata}
                    update_data["extra_data"] = merged_metadata
                else:
                    update_data["extra_data"] = metadata

            stmt = (
                update(MLModelModel)
                .where(MLModelModel.id == model_id)
                .values(**update_data)
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            updated = result.rowcount > 0
            if updated:
                logger.info(
                    "Model status updated", model_id=str(model_id), status=status.value
                )

            return updated

        except Exception as e:
            await self.session.rollback()
            logger.error(
                "Failed to update model status", error=str(e), model_id=str(model_id)
            )
            raise RepositoryError(f"Failed to update model status: {e}") from e

    async def deactivate_model(self, model_id: UUID) -> bool:
        """Deactivate model (soft delete)."""
        try:
            stmt = (
                update(MLModelModel)
                .where(MLModelModel.id == model_id)
                .values(
                    is_active=False,
                    status=ModelStatus.DEPRECATED.value,
                    updated_at=datetime.now(timezone.utc),
                )
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            deactivated = result.rowcount > 0
            if deactivated:
                logger.info("Model deactivated", model_id=str(model_id))

            return deactivated

        except Exception as e:
            await self.session.rollback()
            logger.error(
                "Failed to deactivate model", error=str(e), model_id=str(model_id)
            )
            raise RepositoryError(f"Failed to deactivate model: {e}") from e

    async def find_models_by_performance(
        self,
        model_type: str,
        min_accuracy: Optional[float] = None,
        min_f1_score: Optional[float] = None,
        limit: int = 10,
    ) -> List[MLModelEntity]:
        """Find models by performance criteria."""
        try:
            conditions = [MLModelModel.model_type == model_type]

            if min_accuracy is not None:
                conditions.append(MLModelModel.accuracy >= min_accuracy)

            if min_f1_score is not None:
                conditions.append(MLModelModel.f1_score >= min_f1_score)

            stmt = (
                select(MLModelModel)
                .where(and_(*conditions))
                .order_by(desc(MLModelModel.f1_score), desc(MLModelModel.accuracy))
                .limit(limit)
            )

            result = await self.session.execute(stmt)
            model_dbs = result.scalars().all()

            return [self.mapper.to_entity(model_db) for model_db in model_dbs]

        except Exception as e:
            logger.error("Failed to find models by performance", error=str(e))
            raise RepositoryError(f"Failed to find models by performance: {e}") from e

    async def get_model_statistics(self) -> Dict[str, Any]:
        """Get comprehensive model statistics for monitoring."""
        try:
            # Count by status
            status_stmt = (
                select(MLModelModel.status, func.count(MLModelModel.id).label("count"))
                .where(MLModelModel.is_active == True)
                .group_by(MLModelModel.status)
            )

            # Count by type
            type_stmt = (
                select(
                    MLModelModel.model_type, func.count(MLModelModel.id).label("count")
                )
                .where(MLModelModel.is_active == True)
                .group_by(MLModelModel.model_type)
            )

            # Performance metrics
            perf_stmt = select(
                func.avg(MLModelModel.accuracy).label("avg_accuracy"),
                func.avg(MLModelModel.f1_score).label("avg_f1_score"),
                func.avg(MLModelModel.training_duration_minutes).label(
                    "avg_training_time"
                ),
            ).where(
                and_(
                    MLModelModel.is_active == True,
                    MLModelModel.status.in_(
                        [ModelStatus.TRAINED.value, ModelStatus.DEPLOYED.value]
                    ),
                )
            )

            status_result = await self.session.execute(status_stmt)
            type_result = await self.session.execute(type_stmt)
            perf_result = await self.session.execute(perf_stmt)

            status_counts = {row.status: row.count for row in status_result}
            type_counts = {row.model_type: row.count for row in type_result}

            perf_row = perf_result.first()
            performance_metrics = {
                "average_accuracy": (
                    float(perf_row.avg_accuracy) if perf_row.avg_accuracy else 0.0
                ),
                "average_f1_score": (
                    float(perf_row.avg_f1_score) if perf_row.avg_f1_score else 0.0
                ),
                "average_training_time_minutes": (
                    float(perf_row.avg_training_time)
                    if perf_row.avg_training_time
                    else 0.0
                ),
            }

            return {
                "total_active_models": sum(status_counts.values()),
                "by_status": status_counts,
                "by_type": type_counts,
                "performance_metrics": performance_metrics,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error("Failed to get model statistics", error=str(e))
            raise RepositoryError(f"Failed to get model statistics: {e}") from e

    async def cleanup_old_versions(
        self, model_name: str, keep_versions: int = 5
    ) -> int:
        """Cleanup old model versions, keeping only the latest N versions."""
        try:
            # Find models to keep (latest versions)
            keep_stmt = (
                select(MLModelModel.id)
                .where(MLModelModel.name == model_name)
                .order_by(desc(MLModelModel.created_at))
                .limit(keep_versions)
            )

            keep_result = await self.session.execute(keep_stmt)
            keep_ids = [row.id for row in keep_result]

            if not keep_ids:
                return 0

            # Deactivate old versions
            cleanup_stmt = (
                update(MLModelModel)
                .where(
                    and_(
                        MLModelModel.name == model_name,
                        ~MLModelModel.id.in_(keep_ids),
                        MLModelModel.status
                        != ModelStatus.DEPLOYED.value,  # Don't cleanup deployed models
                    )
                )
                .values(
                    is_active=False,
                    status=ModelStatus.DEPRECATED.value,
                    updated_at=datetime.now(timezone.utc),
                )
            )

            result = await self.session.execute(cleanup_stmt)
            await self.session.commit()

            cleaned_count = result.rowcount
            logger.info(
                "Model versions cleaned up",
                model_name=model_name,
                cleaned_count=cleaned_count,
            )

            return cleaned_count

        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to cleanup old model versions", error=str(e))
            raise RepositoryError(f"Failed to cleanup old model versions: {e}") from e

    async def promote_to_production(self, model_id: UUID) -> bool:
        """Promote model to production and demote current production model."""
        try:
            # Get the model to promote
            model_to_promote = await self.session.get(MLModelModel, model_id)
            if not model_to_promote:
                raise RepositoryError(f"Model {model_id} not found")

            model_type = model_to_promote.model_type

            # Begin transaction for atomic promotion
            # First, demote current production models of same type
            demote_stmt = (
                update(MLModelModel)
                .where(
                    and_(
                        MLModelModel.model_type == model_type,
                        MLModelModel.status == ModelStatus.DEPLOYED.value,
                        MLModelModel.id != model_id,
                    )
                )
                .values(
                    status=ModelStatus.TRAINED.value,
                    updated_at=datetime.now(timezone.utc),
                )
            )

            # Then promote the new model
            promote_stmt = (
                update(MLModelModel)
                .where(MLModelModel.id == model_id)
                .values(
                    status=ModelStatus.DEPLOYED.value,
                    deployed_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    is_active=True,
                )
            )

            demote_result = await self.session.execute(demote_stmt)
            promote_result = await self.session.execute(promote_stmt)

            await self.session.commit()

            promoted = promote_result.rowcount > 0
            if promoted:
                logger.info(
                    "Model promoted to production",
                    model_id=str(model_id),
                    model_type=model_type,
                    demoted_count=demote_result.rowcount,
                )

            return promoted

        except Exception as e:
            await self.session.rollback()
            logger.error(
                "Failed to promote model to production",
                error=str(e),
                model_id=str(model_id),
            )
            raise RepositoryError(f"Failed to promote model to production: {e}") from e
