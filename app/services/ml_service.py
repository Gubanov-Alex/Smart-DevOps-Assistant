"""ML service orchestration layer."""

import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

import structlog

from app.core.interfaces import (
    IAnomalyDetector,
    IIncidentAnalyzer,
    ILogClassifier,
    IModelRegistry,
)
from app.domain.entities import LogEntry, LogLevel
from app.events import AnomalyDetected, EventBus, LogClassificationCompleted

logger = structlog.get_logger()


class MLService:
    """
    Main ML service orchestrator.

    Interview talking point: Service layer orchestration with dependency injection
    """

    def __init__(
        self,
        classifier: ILogClassifier,
        detector: IAnomalyDetector,
        registry: IModelRegistry,
        incident_analyzer: IIncidentAnalyzer,
        event_bus: EventBus,
    ):
        """Initialize ML service constructor."""
        self._classifier = classifier
        self._detector = detector
        self._registry = registry
        self._incident_analyzer = incident_analyzer
        self._event_bus = event_bus
        self._model_cache: Dict[str, Any] = {}
        self._stats = {
            "total_classifications": 0,
            "total_anomalies_detected": 0,
            "average_processing_time": 0.0,
        }

    async def analyze_logs_batch(
        self,
        logs: List[str],
        include_anomaly_detection: bool = True,
        include_incident_analysis: bool = True,
    ) -> Dict[str, Any]:
        """
        Comprehensive batch log analysis.

        Args:
            logs: Raw log messages
            include_anomaly_detection: Run anomaly detection
            include_incident_analysis: Run incident pattern analysis

        Returns:
            Complete analysis results
        """
        start_time = time.time()

        try:
            # Step 1: Log Classification
            logger.info("Starting batch log classification", count=len(logs))

            classifications = await self._classifier.classify(logs)

            # Convert to LogEntry objects for further analysis
            log_entries = [
                LogEntry(
                    message=log,
                    timestamp=datetime.now(timezone.utc),
                    level=level,
                    source="batch_analysis",
                    id=uuid4(),
                )
                for log, level in zip(logs, classifications)
            ]

            results = {
                "classifications": [
                    {
                        "message": entry.message,
                        "level": entry.level.value,
                        "confidence": await self._classifier.get_confidence(entry.message, entry.level),
                        "log_id": str(entry.id),
                    }
                    for entry in log_entries
                ],
                "summary": {
                    "total_logs": len(logs),
                    "error_count": sum(1 for entry in log_entries if entry.level.is_error_level()),
                    "critical_count": sum(1 for entry in log_entries if entry.level == LogLevel.CRITICAL),
                    "warning_count": sum(1 for entry in log_entries if entry.level == LogLevel.WARNING),
                },
            }

            # Step 2: Anomaly Detection (if requested)
            if include_anomaly_detection:
                logger.info("Running anomaly detection")
                anomalies = await self._detector.detect_logs(log_entries)

                results["anomalies"] = [
                    {
                        "score": anomaly.value,
                        "confidence": anomaly.confidence,
                        "severity": anomaly.severity_level(),
                        "is_significant": anomaly.is_significant_anomaly,
                    }
                    for anomaly in anomalies
                ]

                # Publish anomaly events for significant findings
                for anomaly in anomalies:
                    if anomaly.is_significant_anomaly:
                        event = AnomalyDetected(
                            aggregate_id=uuid4(),
                            source="batch_analysis",
                            anomaly_score=anomaly,
                            detection_method="ml_autoencoder",
                            severity=anomaly.severity_level(),
                            affected_logs=[entry.id for entry in log_entries],
                        )
                        await self._event_bus.publish(event)

            # Step 3: Incident Analysis (if requested)
            if include_incident_analysis:
                logger.info("Running incident pattern analysis")
                incident_analysis = await self._incident_analyzer.analyze_incident_pattern(log_entries)
                results["incident_analysis"] = incident_analysis

            # Step 4: Update statistics
            processing_time = time.time() - start_time
            self._stats["total_classifications"] += len(logs)
            self._stats["average_processing_time"] = (self._stats["average_processing_time"] + processing_time) / 2

            results["processing_time_ms"] = processing_time * 1000
            results["timestamp"] = datetime.now(timezone.utc).isoformat()

            # Publish classification events
            for entry in log_entries:
                event = LogClassificationCompleted(
                    aggregate_id=entry.id,
                    log_id=entry.id,
                    predicted_level=entry.level,
                    confidence=await self._classifier.get_confidence(entry.message, entry.level),
                    model_version="v1.0.0",
                    processing_time_ms=int((processing_time / len(logs)) * 1000),
                )
                await self._event_bus.publish(event)

            logger.info(
                "Batch analysis completed",
                logs_processed=len(logs),
                errors_found=results["summary"]["error_count"],
                processing_time_ms=processing_time * 1000,
            )

            return results

        except Exception as e:
            logger.error("Batch analysis failed", error=str(e), logs_count=len(logs))
            raise

    async def analyze_single_log(self, log_message: str) -> Dict[str, Any]:
        """
        Analyze a single log message quickly.

        Args:
            log_message: Raw log message

        Returns:
            Single log analysis result
        """
        start_time = time.time()

        try:
            # Quick classification
            level = await self._classifier.classify_single(log_message)
            confidence = await self._classifier.get_confidence(log_message, level)

            result = {
                "message": log_message,
                "level": level.value,
                "confidence": confidence,
                "is_error": level.is_error_level(),
                "processing_time_ms": (time.time() - start_time) * 1000,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # If it's an error, run a quick anomaly check
            if level.is_error_level():
                log_entry = LogEntry(
                    message=log_message,
                    timestamp=datetime.now(timezone.utc),
                    level=level,
                    source="single_analysis",
                    id=uuid4(),
                )

                anomalies = await self._detector.detect_logs([log_entry])
                if anomalies:
                    result["anomaly_score"] = anomalies[0].value
                    result["anomaly_confidence"] = anomalies[0].confidence

            return result

        except Exception as e:
            logger.error("Single log analysis failed", error=str(e), message=log_message)
            raise

    async def get_service_stats(self) -> Dict[str, Any]:
        """Get ML service statistics."""
        health_checks = await asyncio.gather(
            self._classifier.health_check(),
            self._detector.health_check(),
            return_exceptions=True,
        )

        return {
            "statistics": self._stats.copy(),
            "health": {
                "classifier": (health_checks[0] if not isinstance(health_checks[0], Exception) else False),
                "detector": (health_checks[1] if not isinstance(health_checks[1], Exception) else False),
                "overall": all(check is True for check in health_checks if not isinstance(check, Exception)),
            },
            "cache_info": {
                "cached_models": len(self._model_cache),
                "cache_keys": list(self._model_cache.keys()),
            },
        }

    async def retrain_model(self, model_name: str, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Trigger model retraining.

        Args:
            model_name: Name of a model to retrain
            training_data: New training data

        Returns:
            Retraining job information
        """
        # This would typically trigger a Celery task for actual training
        job_id = str(uuid4())

        logger.info(
            "Model retraining triggered",
            model_name=model_name,
            job_id=job_id,
            training_samples=len(training_data),
        )

        # In a real implementation, this would:
        # 1. Validate training data
        # 2. Submit to Celery worker
        # 3. Return job tracking info

        return {
            "job_id": job_id,
            "model_name": model_name,
            "status": "submitted",
            "estimated_completion": "30-60 minutes",
            "training_samples": len(training_data),
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        }
