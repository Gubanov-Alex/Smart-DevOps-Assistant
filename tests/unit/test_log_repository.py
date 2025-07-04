"""Comprehensive tests for LogRepository implementation with full coverage - FIXED imports."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

# CRITICAL: Import actual classes to trigger coverage
from app.domain.entities import LogEntry as LogEntryEntity
from app.domain.entities import LogLevel
from app.infrastructure.repositories.log_repository import (
    LogRepository,
    RepositoryError,
)
from app.models import LogEntry as LogEntryModel

fake = Faker()


@pytest.fixture
def mock_session():
    """Create mock async session for testing."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.execute = AsyncMock()
    session.get = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def sample_log_entry():
    """Create sample log entry entity for testing."""
    return LogEntryEntity(
        id=uuid4(),
        message=fake.sentence(),
        level=LogLevel.INFO,
        source=fake.word(),
        timestamp=datetime.now(timezone.utc),
        metadata={"test": "data", "user_id": "123"},
    )


@pytest.fixture
def log_repo(mock_session):
    """Create log repository with mock session."""
    return LogRepository(mock_session)


class TestLogRepository:
    """Comprehensive test suite for LogRepository."""

    @pytest.mark.asyncio
    async def test_save_single_log(self, log_repo, mock_session, sample_log_entry):
        """Test saving a single log entry."""
        # Mock the mapper to prevent import issues
        with patch.object(log_repo, "mapper") as mock_mapper:
            mock_model = MagicMock()
            mock_mapper.to_model.return_value = mock_model

            # Execute
            await log_repo.save(sample_log_entry)

            # Verify
            mock_session.add.assert_called_once_with(mock_model)
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_single_log_error_handling(
        self, log_repo, mock_session, sample_log_entry
    ):
        """Test error handling in save operation."""
        # Setup
        with patch.object(log_repo, "mapper") as mock_mapper:
            mock_mapper.to_model.return_value = MagicMock()
            mock_session.commit.side_effect = Exception("DB Error")

            # Execute & Verify
            with pytest.raises(RepositoryError):
                await log_repo.save(sample_log_entry)

            mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_batch_empty_list(self, log_repo, mock_session):
        """Test batch save with empty list."""
        # Execute
        await log_repo.save_batch([])

        # Verify - no database operations should occur
        mock_session.execute.assert_not_called()
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_save_batch_success(self, log_repo, mock_session):
        """Test successful batch save operation."""
        # Setup
        logs = []
        for i in range(5):
            log_entry = LogEntryEntity(
                id=uuid4(),
                message=f"Log message {i}",
                level=LogLevel.INFO,
                source="test_source",
                timestamp=datetime.now(timezone.utc),
                metadata={"batch": i},
            )
            logs.append(log_entry)

        # Execute
        await log_repo.save_batch(logs)

        # Verify
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_batch_large_dataset(self, log_repo, mock_session):
        """Test batch save with large dataset (multiple chunks)."""
        # Setup - create more logs than batch size
        log_repo._batch_size = 3  # Set small batch size for testing
        logs = []
        for i in range(7):  # This will create 3 chunks: 3+3+1
            log_entry = LogEntryEntity(
                id=uuid4(),
                message=f"Log message {i}",
                level=LogLevel.ERROR,
                source="bulk_source",
                timestamp=datetime.now(timezone.utc),
                metadata={"chunk_test": True},
            )
            logs.append(log_entry)

        # Execute
        await log_repo.save_batch(logs)

        # Verify - should execute 3 times (one per chunk)
        assert mock_session.execute.call_count == 3
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_batch_error_handling(
        self, log_repo, mock_session, sample_log_entry
    ):
        """Test error handling in batch save."""
        # Setup
        mock_session.execute.side_effect = Exception("Batch DB Error")

        # Execute & Verify
        with pytest.raises(RepositoryError):
            await log_repo.save_batch([sample_log_entry])

        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_id_found(self, log_repo, mock_session, sample_log_entry):
        """Test finding log entry by ID."""
        # Setup
        mock_model = MagicMock(spec=LogEntryModel)
        mock_model.id = sample_log_entry.id
        mock_model.message = sample_log_entry.message
        mock_model.level = sample_log_entry.level.value
        mock_model.source = sample_log_entry.source
        mock_model.timestamp = sample_log_entry.timestamp
        mock_model.extra_data = sample_log_entry.metadata
        mock_model.anomaly_score = None
        mock_model.created_at = datetime.now(timezone.utc)

        mock_session.get.return_value = mock_model

        # Mock the mapper
        with patch.object(log_repo, "mapper") as mock_mapper:
            mock_mapper.to_entity.return_value = sample_log_entry

            # Execute
            result = await log_repo.find_by_id(sample_log_entry.id)

            # Verify
            assert result is not None
            assert result.id == sample_log_entry.id
            mock_session.get.assert_called_once_with(LogEntryModel, sample_log_entry.id)

    @pytest.mark.asyncio
    async def test_find_by_id_not_found(self, log_repo, mock_session):
        """Test finding non-existent log entry."""
        # Setup
        mock_session.get.return_value = None

        # Execute
        result = await log_repo.find_by_id(uuid4())

        # Verify
        assert result is None

    @pytest.mark.asyncio
    async def test_find_by_id_error_handling(self, log_repo, mock_session):
        """Test error handling in find_by_id."""
        # Setup
        mock_session.get.side_effect = Exception("DB Error")

        # Execute & Verify
        with pytest.raises(RepositoryError):
            await log_repo.find_by_id(uuid4())

    @pytest.mark.asyncio
    async def test_find_by_source(self, log_repo, mock_session):
        """Test finding logs by source."""
        # Setup
        mock_result = MagicMock()
        mock_logs = []
        sample_entities = []

        for i in range(3):
            log_model = MagicMock(spec=LogEntryModel)
            log_model.id = uuid4()
            log_model.message = f"Source log {i}"
            log_model.level = LogLevel.INFO.value
            log_model.source = "test_source"
            log_model.timestamp = datetime.now(timezone.utc)
            log_model.extra_data = {}
            log_model.anomaly_score = None
            log_model.created_at = datetime.now(timezone.utc)
            mock_logs.append(log_model)

            # Create corresponding entity
            entity = LogEntryEntity(
                id=log_model.id,
                message=log_model.message,
                level=LogLevel.INFO,
                source="test_source",
                timestamp=log_model.timestamp,
                metadata={},
            )
            sample_entities.append(entity)

        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        # Mock the mapper
        with patch.object(log_repo, "mapper") as mock_mapper:
            mock_mapper.to_entity.side_effect = sample_entities

            # Execute
            result = await log_repo.find_by_source("test_source", limit=50)

            # Verify
            assert len(result) == 3
            assert all(log.source == "test_source" for log in result)
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_source_error_handling(self, log_repo, mock_session):
        """Test error handling in find_by_source."""
        # Setup
        mock_session.execute.side_effect = Exception("Query Error")

        # Execute & Verify
        with pytest.raises(RepositoryError):
            await log_repo.find_by_source("test_source")

    @pytest.mark.asyncio
    async def test_find_critical_logs(self, log_repo, mock_session):
        """Test finding critical logs."""
        # Setup
        mock_result = MagicMock()
        critical_log = MagicMock(spec=LogEntryModel)
        critical_log.id = uuid4()
        critical_log.message = "Critical error occurred"
        critical_log.level = LogLevel.CRITICAL.value
        critical_log.source = "system"
        critical_log.timestamp = datetime.now(timezone.utc)
        critical_log.extra_data = {}
        critical_log.anomaly_score = None
        critical_log.created_at = datetime.now(timezone.utc)

        mock_result.scalars.return_value.all.return_value = [critical_log]
        mock_session.execute.return_value = mock_result

        # Mock the find_by_levels method that find_critical_logs calls
        with patch.object(log_repo, "find_by_levels") as mock_find_by_levels:
            critical_entity = LogEntryEntity(
                id=critical_log.id,
                message=critical_log.message,
                level=LogLevel.CRITICAL,
                source=critical_log.source,
                timestamp=critical_log.timestamp,
                metadata={},
            )
            mock_find_by_levels.return_value = [critical_entity]

            # Execute
            result = await log_repo.find_critical_logs(since_minutes=30)

            # Verify
            assert len(result) == 1
            assert result[0].level in [LogLevel.ERROR, LogLevel.CRITICAL]

    @pytest.mark.asyncio
    async def test_find_by_time_range(self, log_repo, mock_session):
        """Test finding logs by time range."""
        # Setup
        start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        end_time = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_logs = []
        sample_entities = []

        for i in range(2):
            log_model = MagicMock(spec=LogEntryModel)
            log_model.id = uuid4()
            log_model.message = f"Time range log {i}"
            log_model.level = LogLevel.INFO.value
            log_model.source = "time_test"
            log_model.timestamp = start_time + timedelta(minutes=i * 10)
            log_model.extra_data = {}
            log_model.anomaly_score = None
            log_model.created_at = datetime.now(timezone.utc)
            mock_logs.append(log_model)

            # Create corresponding entity
            entity = LogEntryEntity(
                id=log_model.id,
                message=log_model.message,
                level=LogLevel.INFO,
                source="time_test",
                timestamp=log_model.timestamp,
                metadata={},
            )
            sample_entities.append(entity)

        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        # Mock the mapper
        with patch.object(log_repo, "mapper") as mock_mapper:
            mock_mapper.to_entity.side_effect = sample_entities

            # Execute
            result = await log_repo.find_by_time_range(
                start_time, end_time, limit=500, offset=0
            )

            # Verify
            assert len(result) == 2
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_time_range_error_handling(self, log_repo, mock_session):
        """Test error handling in find_by_time_range."""
        # Setup
        mock_session.execute.side_effect = Exception("Time query error")
        start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        end_time = datetime.now(timezone.utc)

        # Execute & Verify
        with pytest.raises(RepositoryError):
            await log_repo.find_by_time_range(start_time, end_time)

    @pytest.mark.asyncio
    async def test_find_by_level(self, log_repo, mock_session):
        """Test finding logs by specific level."""
        # Mock the find_by_levels method that find_by_level calls
        with patch.object(log_repo, "find_by_levels") as mock_find_by_levels:
            error_entity = LogEntryEntity(
                id=uuid4(),
                message="Error occurred",
                level=LogLevel.ERROR,
                source="app",
                timestamp=datetime.now(timezone.utc),
                metadata={},
            )
            mock_find_by_levels.return_value = [error_entity]

            # Execute
            result = await log_repo.find_by_level(
                LogLevel.ERROR, since_minutes=120, limit=500
            )

            # Verify
            assert len(result) == 1
            assert result[0].level == LogLevel.ERROR

    @pytest.mark.asyncio
    async def test_find_by_levels(self, log_repo, mock_session):
        """Test finding logs by multiple levels."""
        # Setup
        mock_result = MagicMock()
        mock_logs = []
        sample_entities = []

        # Create logs of different levels
        for level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            log_model = MagicMock(spec=LogEntryModel)
            log_model.id = uuid4()
            log_model.message = f"{level.value} message"
            log_model.level = level.value
            log_model.source = "multi_level_test"
            log_model.timestamp = datetime.now(timezone.utc)
            log_model.extra_data = {}
            log_model.anomaly_score = None
            log_model.created_at = datetime.now(timezone.utc)
            mock_logs.append(log_model)

            # Create corresponding entity
            entity = LogEntryEntity(
                id=log_model.id,
                message=log_model.message,
                level=level,
                source="multi_level_test",
                timestamp=log_model.timestamp,
                metadata={},
            )
            sample_entities.append(entity)

        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        # Mock the mapper
        with patch.object(log_repo, "mapper") as mock_mapper:
            mock_mapper.to_entity.side_effect = sample_entities

            # Execute
            result = await log_repo.find_by_levels([LogLevel.ERROR, LogLevel.CRITICAL])

            # Verify
            assert len(result) == 2
            levels = {log.level for log in result}
            assert LogLevel.ERROR in levels
            assert LogLevel.CRITICAL in levels

    @pytest.mark.asyncio
    async def test_find_by_levels_error_handling(self, log_repo, mock_session):
        """Test error handling in find_by_levels."""
        # Setup
        mock_session.execute.side_effect = Exception("Levels query error")

        # Execute & Verify
        with pytest.raises(RepositoryError):
            await log_repo.find_by_levels([LogLevel.ERROR])

    @pytest.mark.asyncio
    async def test_count_by_level_and_time(self, log_repo, mock_session):
        """Test counting logs by level and time."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalar.return_value = 42
        mock_session.execute.return_value = mock_result

        # Execute
        result = await log_repo.count_by_level_and_time(
            LogLevel.ERROR, since_minutes=30
        )

        # Verify
        assert result == 42
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_by_level_and_time_zero_result(self, log_repo, mock_session):
        """Test counting with zero results."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        # Execute
        result = await log_repo.count_by_level_and_time(
            LogLevel.DEBUG, since_minutes=60
        )

        # Verify
        assert result == 0

    @pytest.mark.asyncio
    async def test_count_by_level_and_time_error_handling(self, log_repo, mock_session):
        """Test error handling in count_by_level_and_time."""
        # Setup
        mock_session.execute.side_effect = Exception("Count error")

        # Execute & Verify
        with pytest.raises(RepositoryError):
            await log_repo.count_by_level_and_time(LogLevel.INFO)

    @pytest.mark.asyncio
    async def test_get_log_statistics(self, log_repo, mock_session):
        """Test getting log statistics."""
        # Setup
        # Mock level distribution result
        level_result = MagicMock()
        level_rows = [
            MagicMock(level="ERROR", count=10),
            MagicMock(level="INFO", count=50),
            MagicMock(level="DEBUG", count=20),
            MagicMock(level="CRITICAL", count=2),
        ]
        level_result.fetchall.return_value = level_rows

        # Mock total count result
        total_result = MagicMock()
        total_result.scalar.return_value = 82

        # Setup session to return different results for different queries
        mock_session.execute.side_effect = [level_result, total_result]

        # Execute
        result = await log_repo.get_log_statistics(since_minutes=120)

        # Verify
        assert result["total_logs"] == 82
        assert result["time_window_minutes"] == 120
        assert result["level_distribution"]["ERROR"] == 10
        assert result["level_distribution"]["INFO"] == 50
        assert result["level_distribution"]["DEBUG"] == 20
        assert result["level_distribution"]["CRITICAL"] == 2
        assert result["critical_logs"] == 2
        assert result["error_logs"] == 10
        assert result["error_rate"] == (10 + 2) / 82  # (errors + critical) / total
        assert "generated_at" in result

    @pytest.mark.asyncio
    async def test_get_log_statistics_error_handling(self, log_repo, mock_session):
        """Test error handling in get_log_statistics."""
        # Setup
        mock_session.execute.side_effect = Exception("Statistics error")

        # Execute & Verify
        with pytest.raises(RepositoryError):
            await log_repo.get_log_statistics()

    @pytest.mark.asyncio
    async def test_find_logs_with_anomalies(self, log_repo, mock_session):
        """Test finding logs with anomaly scores."""
        # Setup
        mock_result = MagicMock()
        anomaly_log = MagicMock(spec=LogEntryModel)
        anomaly_log.id = uuid4()
        anomaly_log.message = "Anomalous behavior detected"
        anomaly_log.level = LogLevel.WARNING.value
        anomaly_log.source = "anomaly_detector"
        anomaly_log.timestamp = datetime.now(timezone.utc)
        anomaly_log.extra_data = {"anomaly_details": "suspicious pattern"}
        anomaly_log.anomaly_score = 0.85
        anomaly_log.created_at = datetime.now(timezone.utc)

        mock_result.scalars.return_value.all.return_value = [anomaly_log]
        mock_session.execute.return_value = mock_result

        # Mock the mapper
        anomaly_entity = LogEntryEntity(
            id=anomaly_log.id,
            message=anomaly_log.message,
            level=LogLevel.WARNING,
            source=anomaly_log.source,
            timestamp=anomaly_log.timestamp,
            metadata=anomaly_log.extra_data,
        )

        with patch.object(log_repo, "mapper") as mock_mapper:
            mock_mapper.to_entity.return_value = anomaly_entity

            # Execute
            result = await log_repo.find_logs_with_anomalies(threshold=0.8, limit=50)

            # Verify
            assert len(result) == 1
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_logs_with_anomalies_error_handling(
        self, log_repo, mock_session
    ):
        """Test error handling in find_logs_with_anomalies."""
        # Setup
        mock_session.execute.side_effect = Exception("Anomaly query error")

        # Execute & Verify
        with pytest.raises(RepositoryError):
            await log_repo.find_logs_with_anomalies()

    @pytest.mark.asyncio
    async def test_delete_old_logs(self, log_repo, mock_session):
        """Test deleting old logs."""
        # Setup
        mock_result = MagicMock()
        mock_result.rowcount = 100
        mock_session.execute.return_value = mock_result

        # Execute
        result = await log_repo.delete_old_logs(older_than_days=30)

        # Verify
        assert result == 100
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_old_logs_error_handling(self, log_repo, mock_session):
        """Test error handling in delete_old_logs."""
        # Setup
        mock_session.execute.side_effect = Exception("Delete error")

        # Execute & Verify
        with pytest.raises(RepositoryError):
            await log_repo.delete_old_logs()

        mock_session.rollback.assert_called_once()


pytestmark = [pytest.mark.asyncio, pytest.mark.unit]
