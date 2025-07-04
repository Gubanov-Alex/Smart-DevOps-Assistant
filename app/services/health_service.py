"""Health check service for monitoring system status."""

import time
from datetime import datetime
from typing import Optional

import psutil
import structlog

from app.core.config import get_settings
from app.database.session import db_manager
from app.schemas.responses.health import (
    DatabaseHealth,
    HealthCheckResponse,
    MLModelsHealth,
    RedisHealth,
    SimpleHealthResponse,
    SystemMetrics,
)

logger = structlog.get_logger(__name__)


class HealthCheckService:
    """Service for performing comprehensive health checks."""

    def __init__(self):
        self.settings = get_settings()
        self.startup_time = time.time()

    async def get_health_status(
        self, include_details: bool = True, request_id: Optional[str] = None
    ) -> HealthCheckResponse:
        """Get comprehensive health status of all system components.

        Args:
            include_details: Whether to include detailed metrics
            request_id: Optional request ID for tracking

        Returns:
            Complete health check response
        """
        start_time = time.time()

        try:
            # Run health checks sequentially to avoid issues
            db_health = await self._check_database_health()
            redis_health = await self._check_redis_health()
            ml_health = await self._check_ml_models_health()

            # Get system metrics (synchronous)
            if include_details:
                system_metrics = self._get_system_metrics()
            else:
                system_metrics = self._get_basic_metrics()

            # Determine overall status
            overall_status = self._determine_overall_status(
                db_health, redis_health, ml_health
            )

            response_time = (time.time() - start_time) * 1000

            response = HealthCheckResponse(
                status=overall_status,
                timestamp=datetime.now().replace(microsecond=0),
                version=self.settings.api_version,
                environment=self.settings.environment,
                uptime_seconds=time.time() - self.startup_time,
                database=db_health,
                redis=redis_health,
                ml_models=ml_health,
                system=system_metrics,
                request_id=request_id,
            )

            logger.info(
                "Health check completed",
                status=overall_status,
                response_time_ms=response_time,
                request_id=request_id,
            )

            return response

        except Exception as e:
            logger.error("Health check failed", error=str(e), request_id=request_id)

            # Return minimal error response
            return HealthCheckResponse(
                status="unhealthy",
                timestamp=datetime.now().replace(microsecond=0),
                version=self.settings.api_version,
                environment=self.settings.environment,
                uptime_seconds=time.time() - self.startup_time,
                database=DatabaseHealth(status="unknown", error="Health check failed"),
                redis=RedisHealth(status="unknown", error="Health check failed"),
                ml_models=MLModelsHealth(status="unknown", error="Health check failed"),
                system=SystemMetrics(
                    memory_usage_mb=0,
                    memory_total_mb=0,
                    memory_percent=0,
                    cpu_usage_percent=0,
                    disk_usage_gb=0,
                    disk_total_gb=0,
                    disk_percent=0,
                ),
                request_id=request_id,
            )

    async def get_simple_health(self) -> SimpleHealthResponse:
        """Get simple health status for load balancers.

        Returns:
            Simple health response with basic status
        """
        try:
            # Quick database connectivity check
            is_db_healthy = await db_manager.health_check()

            status = "ok" if is_db_healthy else "error"

            return SimpleHealthResponse(
                status=status, timestamp=datetime.now().replace(microsecond=0)
            )

        except Exception as e:
            logger.error("Simple health check failed", error=str(e))
            return SimpleHealthResponse(
                status="error", timestamp=datetime.now().replace(microsecond=0)
            )

    async def _check_database_health(self) -> DatabaseHealth:
        """Check database connectivity and performance."""
        start_time = time.time()

        try:
            # Use database manager's health check to avoid import issues
            is_healthy = await db_manager.health_check()

            if is_healthy:
                # Get pool status
                pool_status = db_manager.get_pool_status()
                response_time = (time.time() - start_time) * 1000

                return DatabaseHealth(
                    status="healthy",
                    response_time_ms=response_time,
                    pool_size=pool_status.get("size", 0),
                    active_connections=pool_status.get("checked_out", 0),
                    version="PostgreSQL",  # Simplified for now
                    details=pool_status,
                )
            else:
                response_time = (time.time() - start_time) * 1000
                return DatabaseHealth(
                    status="unhealthy",
                    response_time_ms=response_time,
                    error="Database connection failed",
                )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error("Database health check failed", error=str(e))

            return DatabaseHealth(
                status="unhealthy",
                response_time_ms=response_time,
                error=str(e),
            )

    async def _check_redis_health(self) -> RedisHealth:
        """Check Redis connectivity and performance."""
        start_time = time.time()

        try:
            # TODO: Implement Redis health check when Redis client is added
            # For now, return simulated health status

            response_time = (time.time() - start_time) * 1000

            return RedisHealth(
                status="healthy",
                response_time_ms=response_time,
                memory_usage_mb=50.0,  # Placeholder
                connected_clients=1,  # Placeholder
                keyspace_hits=0,  # Placeholder
                details={"note": "Redis health check not implemented yet"},
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error("Redis health check failed", error=str(e))

            return RedisHealth(
                status="unhealthy",
                response_time_ms=response_time,
                error=str(e),
            )

    async def _check_ml_models_health(self) -> MLModelsHealth:
        """Check ML models availability and status."""
        start_time = time.time()

        try:
            # TODO: Implement ML models health check
            # This will check loaded models, their status, and last prediction time

            response_time = (time.time() - start_time) * 1000

            return MLModelsHealth(
                status="healthy",
                response_time_ms=response_time,
                loaded_models=0,  # Placeholder
                models_status={},  # Placeholder
                last_prediction_at=None,  # Placeholder
                details={"note": "ML models health check not implemented yet"},
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error("ML models health check failed", error=str(e))

            return MLModelsHealth(
                status="unhealthy",
                response_time_ms=response_time,
                error=str(e),
            )

    def _get_system_metrics(self) -> SystemMetrics:
        """Get detailed system performance metrics."""
        try:
            # Memory metrics
            memory = psutil.virtual_memory()

            # CPU metrics (use interval=None for instant reading)
            cpu_percent = psutil.cpu_percent(interval=None)

            # Disk metrics
            disk = psutil.disk_usage("/")

            return SystemMetrics(
                memory_usage_mb=round(memory.used / (1024 * 1024), 2),
                memory_total_mb=round(memory.total / (1024 * 1024), 2),
                memory_percent=round(memory.percent, 2),
                cpu_usage_percent=round(cpu_percent, 2),
                disk_usage_gb=round(disk.used / (1024 * 1024 * 1024), 2),
                disk_total_gb=round(disk.total / (1024 * 1024 * 1024), 2),
                disk_percent=round((disk.used / disk.total) * 100, 2),
            )

        except Exception as e:
            logger.error("Failed to collect system metrics", error=str(e))
            # Return default values instead of raising
            return SystemMetrics(
                memory_usage_mb=0.0,
                memory_total_mb=0.0,
                memory_percent=0.0,
                cpu_usage_percent=0.0,
                disk_usage_gb=0.0,
                disk_total_gb=0.0,
                disk_percent=0.0,
            )

    def _get_basic_metrics(self) -> SystemMetrics:
        """Get basic system metrics for simple health checks."""
        try:
            memory = psutil.virtual_memory()

            return SystemMetrics(
                memory_usage_mb=round(memory.used / (1024 * 1024), 2),
                memory_total_mb=round(memory.total / (1024 * 1024), 2),
                memory_percent=round(memory.percent, 2),
                cpu_usage_percent=0.0,  # Skip CPU check for speed
                disk_usage_gb=0.0,  # Skip disk check for speed
                disk_total_gb=0.0,  # Skip disk check for speed
                disk_percent=0.0,  # Skip disk check for speed
            )

        except Exception as e:
            logger.error("Failed to collect basic metrics", error=str(e))
            # Return default values instead of raising
            return SystemMetrics(
                memory_usage_mb=0.0,
                memory_total_mb=0.0,
                memory_percent=0.0,
                cpu_usage_percent=0.0,
                disk_usage_gb=0.0,
                disk_total_gb=0.0,
                disk_percent=0.0,
            )

    def _determine_overall_status(
        self,
        db_health: DatabaseHealth,
        redis_health: RedisHealth,
        ml_health: MLModelsHealth,
    ) -> str:
        """Determine overall system status based on component health.

        Args:
            db_health: Database health status
            redis_health: Redis health status
            ml_health: ML models health status

        Returns:
            Overall status: healthy, degraded, or unhealthy
        """
        # Critical services that must be healthy
        critical_services = [db_health.status]

        # Non-critical services that can be degraded
        non_critical_services = [redis_health.status, ml_health.status]

        # If any critical service is unhealthy, system is unhealthy
        if any(status == "unhealthy" for status in critical_services):
            return "unhealthy"

        # If any service is degraded/unhealthy, system is degraded
        all_services = critical_services + non_critical_services
        if any(status in ["degraded", "unhealthy"] for status in all_services):
            return "degraded"

        # All services healthy
        return "healthy"


# Global health service instance
health_service = HealthCheckService()
