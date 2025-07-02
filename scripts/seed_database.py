#!/usr/bin/env python3
"""Database seeding script for Smart DevOps Assistant.

This script generates realistic test data for development and testing purposes.
It creates log entries, incidents, and ML models with proper relationships.
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta
from typing import List

import structlog
from faker import Faker

from app.database.session import database_session
from app.models import (
    LogEntry, Incident, MLModel,
    LogLevel, IncidentSeverity, IncidentStatus, ModelStatus
)

logger = structlog.get_logger()
fake = Faker()


class DatabaseSeeder:
    """Database seeding utility with realistic test data generation."""

    def __init__(self):
        self.sources = [
            "api-gateway", "auth-service", "payment-service", "user-service",
            "database-primary", "database-replica", "redis-cache", "message-queue",
            "notification-service", "analytics-service", "ml-pipeline", "monitoring"
        ]

        self.error_messages = [
            "Connection timeout to database",
            "Failed to authenticate user",
            "Payment processing failed",
            "Memory usage exceeded threshold",
            "Disk space running low",
            "API rate limit exceeded",
            "SSL certificate validation failed",
            "Cache miss ratio too high",
            "Queue processing backlog detected",
            "External service unavailable"
        ]

        self.info_messages = [
            "User logged in successfully",
            "Payment processed successfully",
            "Cache hit for user data",
            "Background job completed",
            "Health check passed",
            "Configuration reloaded",
            "Backup completed successfully",
            "Metrics exported to monitoring",
            "Session created for user",
            "API request processed"
        ]

        self.warning_messages = [
            "High memory usage detected",
            "Slow query execution time",
            "Retry attempt for failed operation",
            "Deprecated API endpoint used",
            "Cache eviction due to memory pressure",
            "Connection pool nearly exhausted",
            "Rate limiting applied to client",
            "Disk usage approaching limit",
            "Background job taking longer than expected",
            "SSL certificate expires soon"
        ]

    async def seed_log_entries(self, count: int = 1000) -> List[LogEntry]:
        """Generate realistic log entries."""
        logger.info("Generating log entries", count=count)

        entries = []
        base_time = datetime.utcnow() - timedelta(days=7)

        for i in range(count):
            # Distribute log levels realistically
            level_weights = {
                LogLevel.INFO: 0.5,
                LogLevel.WARNING: 0.25,
                LogLevel.ERROR: 0.15,
                LogLevel.DEBUG: 0.08,
                LogLevel.CRITICAL: 0.02
            }
            level = random.choices(
                list(level_weights.keys()),
                weights=list(level_weights.values())
            )[0]

            # Choose appropriate message based on level
            if level == LogLevel.ERROR or level == LogLevel.CRITICAL:
                message = random.choice(self.error_messages)
            elif level == LogLevel.WARNING:
                message = random.choice(self.warning_messages)
            else:
                message = random.choice(self.info_messages)

            # Add realistic variations to messages
            if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                message += f" (error_code: {random.randint(1000, 9999)})"

            # Generate timestamp with realistic distribution
            # More recent logs are more likely
            time_offset = random.betavariate(2, 5) * 7 * 24 * 3600  # Beta distribution for time
            timestamp = base_time + timedelta(seconds=time_offset)

            # Generate metadata based on source
            source = random.choice(self.sources)
            extra_data = self._generate_metadata(source, level)

            entry = LogEntry(
                message=message,
                level=level,
                source=source,
                timestamp=timestamp,
                extra_data=extra_data,
                processing_time_ms=random.uniform(1.0, 50.0),
                classification_confidence=random.uniform(0.8, 1.0) if random.random() > 0.3 else None,
                anomaly_score=random.uniform(0.0, 1.0) if level in [LogLevel.ERROR, LogLevel.CRITICAL] else None
            )
            entries.append(entry)

        async with database_session() as session:
            session.add_all(entries)
            await session.commit()
            logger.info("Log entries created successfully", count=len(entries))

        return entries

    async def seed_incidents(self, count: int = 50, log_entries: List[LogEntry] = None) -> List[Incident]:
        """Generate realistic incidents."""
        logger.info("Generating incidents", count=count)

        incidents = []
        incident_templates = [
            {
                "title": "Database Connection Issues",
                "description": "Multiple connection timeouts to primary database",
                "severity": IncidentSeverity.HIGH,
                "tags": ["database", "connectivity", "performance"]
            },
            {
                "title": "Payment Processing Failures",
                "description": "High rate of payment processing failures detected",
                "severity": IncidentSeverity.CRITICAL,
                "tags": ["payment", "financial", "customer-impact"]
            },
            {
                "title": "API Rate Limiting Issues",
                "description": "Unusual spike in API rate limit violations",
                "severity": IncidentSeverity.MEDIUM,
                "tags": ["api", "rate-limiting", "performance"]
            },
            {
                "title": "SSL Certificate Expiration",
                "description": "SSL certificates for multiple services expiring soon",
                "severity": IncidentSeverity.LOW,
                "tags": ["security", "ssl", "maintenance"]
            },
            {
                "title": "Memory Usage Spike",
                "description": "Abnormal memory usage patterns detected across services",
                "severity": IncidentSeverity.MEDIUM,
                "tags": ["memory", "performance", "infrastructure"]
            }
        ]

        for i in range(count):
            template = random.choice(incident_templates)

            # Generate realistic timestamps
            created_at = fake.date_time_between(start_date="-7d", end_date="now")

            # Determine status based on age
            age_hours = (datetime.utcnow() - created_at).total_seconds() / 3600
            if age_hours > 48:
                status = random.choice([IncidentStatus.RESOLVED, IncidentStatus.CLOSED])
                resolved_at = created_at + timedelta(hours=random.uniform(1, 24))
            elif age_hours > 12:
                status = random.choice([IncidentStatus.IN_PROGRESS, IncidentStatus.RESOLVED])
                resolved_at = created_at + timedelta(
                    hours=random.uniform(1, 12)) if status == IncidentStatus.RESOLVED else None
            else:
                status = random.choice([IncidentStatus.OPEN, IncidentStatus.IN_PROGRESS])
                resolved_at = None

            incident = Incident(
                title=f"{template['title']} #{i + 1}",
                description=template["description"] + f" (Instance {i + 1})",
                severity=template["severity"],
                status=status,
                source=random.choice(self.sources),
                created_at=created_at,
                resolved_at=resolved_at,
                assigned_to=fake.email() if random.random() > 0.3 else None,
                tags=template["tags"] + [fake.word() for _ in range(random.randint(0, 2))],
                extra_data={
                    "reporter": fake.email(),
                    "affected_users": random.randint(10, 5000) if template["severity"] in [IncidentSeverity.HIGH,
                                                                                           IncidentSeverity.CRITICAL] else random.randint(
                        1, 100),
                    "priority": random.randint(1, 10),
                    "escalated": random.choice([True, False])
                },
                priority_score=self._calculate_priority_score(template["severity"])
            )
            incidents.append(incident)

        async with database_session() as session:
            session.add_all(incidents)
            await session.commit()

            # Associate some incidents with log entries if provided
            if log_entries:
                await self._associate_logs_with_incidents(session, incidents, log_entries)

            logger.info("Incidents created successfully", count=len(incidents))

        return incidents

    async def seed_ml_models(self, count: int = 20) -> List[MLModel]:
        """Generate ML model registry entries."""
        logger.info("Generating ML models", count=count)

        models = []
        model_types = [
            ("log-classifier", "classification"),
            ("anomaly-detector", "anomaly_detection"),
            ("incident-predictor", "prediction"),
            ("performance-analyzer", "regression"),
            ("text-classifier", "nlp_classification"),
            ("time-series-forecaster", "forecasting")
        ]

        for model_name, model_type in model_types:
            # Generate multiple versions for each model
            versions_count = random.randint(2, 5)

            for version_num in range(1, versions_count + 1):
                version = f"{version_num}.{random.randint(0, 9)}.{random.randint(0, 9)}"

                # Determine status based on version (latest more likely to be active)
                if version_num == versions_count:
                    status = random.choice([ModelStatus.DEPLOYED, ModelStatus.READY])
                    is_active = status == ModelStatus.DEPLOYED
                elif version_num == versions_count - 1:
                    status = random.choice([ModelStatus.READY, ModelStatus.TRAINED])
                    is_active = False
                else:
                    status = random.choice([ModelStatus.DEPRECATED, ModelStatus.TRAINED])
                    is_active = False

                # Generate realistic performance metrics
                base_accuracy = random.uniform(0.75, 0.95)
                accuracy = base_accuracy + random.uniform(-0.05, 0.05)
                precision = accuracy + random.uniform(-0.03, 0.03)
                recall = accuracy + random.uniform(-0.03, 0.03)
                f1_score = 2 * (precision * recall) / (precision + recall)

                # Ensure all metrics are within valid range
                accuracy = max(0.0, min(1.0, accuracy))
                precision = max(0.0, min(1.0, precision))
                recall = max(0.0, min(1.0, recall))
                f1_score = max(0.0, min(1.0, f1_score))

                created_at = fake.date_time_between(start_date="-90d", end_date="-1d")
                trained_at = created_at + timedelta(hours=random.uniform(1, 24))
                deployed_at = trained_at + timedelta(
                    hours=random.uniform(0.5, 48)) if status == ModelStatus.DEPLOYED else None

                model = MLModel(
                    name=model_name,
                    version=version,
                    model_type=model_type,
                    status=status,
                    created_at=created_at,
                    trained_at=trained_at,
                    deployed_at=deployed_at,
                    accuracy=accuracy,
                    precision=precision,
                    recall=recall,
                    f1_score=f1_score,
                    training_dataset_size=random.randint(10000, 100000),
                    training_duration_minutes=random.randint(15, 480),
                    is_active=is_active,
                    model_path=f"/models/{model_name}/{version}/model.pkl",
                    config={
                        "algorithm": random.choice(["random_forest", "gradient_boosting", "neural_network", "svm"]),
                        "hyperparameters": {
                            "learning_rate": random.uniform(0.001, 0.1),
                            "n_estimators": random.randint(50, 200),
                            "max_depth": random.randint(5, 20)
                        },
                        "features": random.randint(10, 50)
                    },
                    extra_data={
                        "framework": random.choice(["scikit-learn", "tensorflow", "pytorch", "xgboost"]),
                        "python_version": "3.12",
                        "training_time": f"{random.randint(30, 480)} minutes",
                        "data_version": f"v{random.randint(1, 10)}",
                        "experiment_id": str(uuid.uuid4())
                    },
                    deployment_config={
                        "endpoint": f"/api/v1/models/{model_name}/predict",
                        "timeout": 30,
                        "batch_size": random.randint(32, 256),
                        "auto_scaling": True
                    } if status == ModelStatus.DEPLOYED else None
                )
                models.append(model)

        async with database_session() as session:
            session.add_all(models)
            await session.commit()
            logger.info("ML models created successfully", count=len(models))

        return models

    def _generate_metadata(self, source: str, level: LogLevel) -> dict:
        """Generate realistic metadata based on source and level."""
        base_metadata = {
            "hostname": fake.hostname(),
            "process_id": random.randint(1000, 9999),
            "thread_id": random.randint(1, 100)
        }

        if "api" in source or "service" in source:
            base_metadata.update({
                "request_id": str(uuid.uuid4()),
                "user_id": str(random.randint(1000, 99999)),
                "endpoint": f"/api/v1/{fake.word()}",
                "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
                "status_code": random.choice(
                    [200, 201, 400, 401, 403, 404, 500]) if level == LogLevel.ERROR else random.choice([200, 201, 202])
            })

        if "database" in source:
            base_metadata.update({
                "query_duration_ms": random.uniform(10, 1000),
                "rows_affected": random.randint(0, 1000),
                "connection_pool_size": random.randint(5, 50)
            })

        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            base_metadata.update({
                "error_code": f"E{random.randint(1000, 9999)}",
                "stack_trace_available": True,
                "retry_count": random.randint(0, 3)
            })

        return base_metadata

    def _calculate_priority_score(self, severity: IncidentSeverity) -> float:
        """Calculate realistic priority score based on severity."""
        base_scores = {
            IncidentSeverity.LOW: 0.2,
            IncidentSeverity.MEDIUM: 0.5,
            IncidentSeverity.HIGH: 0.8,
            IncidentSeverity.CRITICAL: 0.95
        }

        base_score = base_scores.get(severity, 0.5)
        # Add some randomness
        return min(1.0, max(0.0, base_score + random.uniform(-0.1, 0.1)))

    async def _associate_logs_with_incidents(
            self,
            session,
            incidents: List[Incident],
            log_entries: List[LogEntry]
    ):
        """Associate relevant log entries with incidents."""
        logger.info("Associating logs with incidents")

        # Filter error and critical logs for association
        error_logs = [log for log in log_entries if log.level in [LogLevel.ERROR, LogLevel.CRITICAL]]

        for incident in incidents:
            # Associate 1-5 random error logs with each incident
            num_logs = random.randint(1, min(5, len(error_logs)))
            associated_logs = random.sample(error_logs, num_logs)

            incident.related_logs.extend(associated_logs)

        await session.commit()
        logger.info("Log-incident associations created")

    async def seed_all(
            self,
            log_count: int = 1000,
            incident_count: int = 50,
            model_count: int = 20
    ):
        """Seed all data types."""
        logger.info("Starting complete database seeding")

        # Seed in order to handle relationships
        log_entries = await self.seed_log_entries(log_count)
        incidents = await self.seed_incidents(incident_count, log_entries)
        models = await self.seed_ml_models(model_count)

        logger.info(
            "Database seeding completed",
            logs=len(log_entries),
            incidents=len(incidents),
            models=len(models)
        )

        return {
            "log_entries": len(log_entries),
            "incidents": len(incidents),
            "ml_models": len(models)
        }


async def main():
    """Main seeding function."""
    import argparse

    parser = argparse.ArgumentParser(description="Seed Smart DevOps Assistant database")
    parser.add_argument("--logs", type=int, default=1000, help="Number of log entries to create")
    parser.add_argument("--incidents", type=int, default=50, help="Number of incidents to create")
    parser.add_argument("--models", type=int, default=20, help="Number of ML models to create")
    parser.add_argument("--all", action="store_true", help="Seed all data types")

    args = parser.parse_args()

    seeder = DatabaseSeeder()

    if args.all:
        results = await seeder.seed_all(args.logs, args.incidents, args.models)
        print(f"Seeding completed: {results}")
    else:
        print("Use --all flag to seed the database")


if __name__ == "__main__":
    asyncio.run(main())
