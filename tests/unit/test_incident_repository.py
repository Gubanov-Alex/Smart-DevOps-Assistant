"""Tests for IncidentRepository implementation."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Incident as IncidentEntity
from app.domain.entities import (
    IncidentSeverity,
    IncidentStatus,
)
from app.infrastructure.repositories.incident_repository import (
    IncidentRepository,
    RepositoryError,
)
from app.models import Incident as IncidentModel

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
def sample_incident():
    """Create sample incident entity for testing."""
    return IncidentEntity(
        id=uuid4(),
        title=fake.sentence(),
        description=fake.text(),
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.OPEN,
        source=fake.word(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        resolved_at=None,
        assigned_to=fake.name(),
        tags=[fake.word(), fake.word()],
        related_logs=[],
        metadata={"test": "data"},
    )


@pytest.fixture
def incident_repo(mock_session):
    """Create incident repository with mock session."""
    return IncidentRepository(mock_session)


class TestIncidentRepository:
    """Test suite for IncidentRepository."""

    @pytest.mark.asyncio
    async def test_save_new_incident(
        self, incident_repo, mock_session, sample_incident
    ):
        """Test saving a new incident."""
        # Setup
        mock_session.get.return_value = None

        # Execute
        await incident_repo.save(sample_incident)

        # Verify
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_existing_incident(
        self, incident_repo, mock_session, sample_incident
    ):
        """Test updating an existing incident."""
        # Setup
        existing_model = MagicMock(spec=IncidentModel)
        mock_session.get.return_value = existing_model

        # Execute
        await incident_repo.save(sample_incident)

        # Verify
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_id_found(self, incident_repo, mock_session, sample_incident):
        """Test finding incident by ID."""
        # Setup
        mock_result = MagicMock()
        mock_incident = MagicMock(spec=IncidentModel)
        mock_incident.id = sample_incident.id
        mock_incident.title = sample_incident.title
        mock_incident.description = sample_incident.description
        mock_incident.severity = sample_incident.severity.value
        mock_incident.status = sample_incident.status.value
        mock_incident.source = sample_incident.source
        mock_incident.created_at = sample_incident.created_at
        mock_incident.updated_at = sample_incident.updated_at
        mock_incident.resolved_at = sample_incident.resolved_at
        mock_incident.assigned_to = sample_incident.assigned_to
        mock_incident.tags = sample_incident.tags
        mock_incident.extra_data = sample_incident.metadata
        mock_incident.related_logs = []

        mock_result.scalar_one_or_none.return_value = mock_incident
        mock_session.execute.return_value = mock_result

        # Execute
        result = await incident_repo.find_by_id(sample_incident.id)

        # Verify
        assert result is not None
        assert result.id == sample_incident.id

    @pytest.mark.asyncio
    async def test_find_by_id_not_found(self, incident_repo, mock_session):
        """Test finding non-existent incident."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Execute
        result = await incident_repo.find_by_id(uuid4())

        # Verify
        assert result is None

    @pytest.mark.asyncio
    async def test_find_open_incidents(self, incident_repo, mock_session):
        """Test finding open incidents."""
        # Setup
        mock_result = MagicMock()
        mock_incidents = []
        for i in range(2):
            incident = MagicMock(spec=IncidentModel)
            incident.id = uuid4()
            incident.title = f"Incident {i}"
            incident.description = f"Description {i}"
            incident.severity = IncidentSeverity.HIGH.value
            incident.status = IncidentStatus.OPEN.value
            incident.source = "test"
            incident.created_at = datetime.now(timezone.utc)
            incident.updated_at = datetime.now(timezone.utc)
            incident.resolved_at = None
            incident.assigned_to = "user"
            incident.tags = []
            incident.extra_data = {}
            incident.related_logs = []
            mock_incidents.append(incident)

        mock_result.scalars.return_value.all.return_value = mock_incidents
        mock_session.execute.return_value = mock_result

        # Execute
        result = await incident_repo.find_open_incidents()

        # Verify
        assert len(result) == 2
        assert all(inc.status == IncidentStatus.OPEN for inc in result)

    @pytest.mark.asyncio
    async def test_update_status_success(self, incident_repo, mock_session):
        """Test successful status update."""
        # Setup
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        # Execute
        result = await incident_repo.update_status(uuid4(), IncidentStatus.RESOLVED)

        # Verify
        assert result is True
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling(self, incident_repo, mock_session, sample_incident):
        """Test error handling."""
        # Setup
        mock_session.get.side_effect = Exception("DB Error")

        # Execute & Verify
        with pytest.raises(RepositoryError):
            await incident_repo.save(sample_incident)

        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_severity(self, incident_repo, mock_session):
        """Test finding incidents by severity."""
        # Setup
        mock_result = MagicMock()
        high_severity_incident = MagicMock(spec=IncidentModel)
        high_severity_incident.id = uuid4()
        high_severity_incident.title = "High Severity Issue"
        high_severity_incident.description = "Critical system failure"
        high_severity_incident.severity = IncidentSeverity.HIGH.value
        high_severity_incident.status = IncidentStatus.OPEN.value
        high_severity_incident.source = "monitoring"
        high_severity_incident.created_at = datetime.now(timezone.utc)
        high_severity_incident.updated_at = datetime.now(timezone.utc)
        high_severity_incident.resolved_at = None
        high_severity_incident.assigned_to = "ops_team"
        high_severity_incident.tags = ["critical", "system"]
        high_severity_incident.extra_data = {}
        high_severity_incident.related_logs = []

        mock_result.scalars.return_value.all.return_value = [high_severity_incident]
        mock_session.execute.return_value = mock_result

        # Execute
        result = await incident_repo.find_by_severity(IncidentSeverity.HIGH)

        # Verify
        assert len(result) == 1
        assert result[0].severity == IncidentSeverity.HIGH

    @pytest.mark.asyncio
    async def test_find_critical_incidents(self, incident_repo, mock_session):
        """Test finding critical incidents within time period."""
        # Setup
        mock_result = MagicMock()
        critical_incident = MagicMock(spec=IncidentModel)
        critical_incident.id = uuid4()
        critical_incident.title = "Critical System Outage"
        critical_incident.description = "Complete system unavailable"
        critical_incident.severity = IncidentSeverity.CRITICAL.value
        critical_incident.status = IncidentStatus.OPEN.value
        critical_incident.source = "alertmanager"
        critical_incident.created_at = datetime.now(timezone.utc)
        critical_incident.updated_at = datetime.now(timezone.utc)
        critical_incident.resolved_at = None
        critical_incident.assigned_to = "oncall_engineer"
        critical_incident.tags = ["outage", "p1"]
        critical_incident.extra_data = {}
        critical_incident.related_logs = []
        critical_incident.priority_score = 100

        mock_result.scalars.return_value.all.return_value = [critical_incident]
        mock_session.execute.return_value = mock_result

        # Execute
        result = await incident_repo.find_critical_incidents(since_hours=6)

        # Verify
        assert len(result) == 1
        assert result[0].severity == IncidentSeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_find_by_time_range(self, incident_repo, mock_session):
        """Test finding incidents by time range."""
        # Setup
        start_time = datetime.now(timezone.utc) - timedelta(days=1)
        end_time = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_incidents = []
        for i in range(3):
            incident = MagicMock(spec=IncidentModel)
            incident.id = uuid4()
            incident.title = f"Time Range Incident {i}"
            incident.description = f"Description {i}"
            incident.severity = IncidentSeverity.MEDIUM.value
            incident.status = IncidentStatus.RESOLVED.value
            incident.source = "scheduler"
            incident.created_at = start_time + timedelta(hours=i * 2)
            incident.updated_at = datetime.now(timezone.utc)
            incident.resolved_at = datetime.now(timezone.utc)
            incident.assigned_to = "dev_team"
            incident.tags = []
            incident.extra_data = {}
            incident.related_logs = []
            mock_incidents.append(incident)

        mock_result.scalars.return_value.all.return_value = mock_incidents
        mock_session.execute.return_value = mock_result

        # Execute
        result = await incident_repo.find_by_time_range(
            start_time, end_time, limit=100, offset=0
        )

        # Verify
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_assign_incident(self, incident_repo, mock_session):
        """Test assigning incident to team member."""
        # Setup
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        # Execute
        result = await incident_repo.assign_incident(uuid4(), "john.doe@company.com")

        # Verify
        assert result is True
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_incident_statistics(self, incident_repo, mock_session):
        """Test getting incident statistics."""
        # Setup
        # Mock status counts
        status_result = MagicMock()
        status_rows = [
            MagicMock(status="OPEN", count=5),
            MagicMock(status="IN_PROGRESS", count=3),
            MagicMock(status="RESOLVED", count=15),
        ]
        status_result.__iter__ = lambda self: iter(status_rows)

        # Mock severity counts
        severity_result = MagicMock()
        severity_rows = [
            MagicMock(severity="HIGH", count=8),
            MagicMock(severity="MEDIUM", count=10),
            MagicMock(severity="LOW", count=5),
        ]
        severity_result.__iter__ = lambda self: iter(severity_rows)

        # Mock resolution time
        resolution_result = MagicMock()
        resolution_result.scalar.return_value = 45.5

        mock_session.execute.side_effect = [
            status_result,
            severity_result,
            resolution_result,
        ]

        # Execute
        result = await incident_repo.get_incident_statistics(since_hours=48)

        # Verify
        assert result["total_incidents"] == 23  # 5+3+15
        assert result["by_status"]["OPEN"] == 5
        assert result["by_severity"]["HIGH"] == 8
        assert result["average_resolution_time_minutes"] == 45.5
        assert result["since_hours"] == 48

    @pytest.mark.asyncio
    async def test_bulk_update_status(self, incident_repo, mock_session):
        """Test bulk status update."""
        # Setup
        incident_ids = [uuid4(), uuid4(), uuid4()]
        mock_result = MagicMock()
        mock_result.rowcount = 3
        mock_session.execute.return_value = mock_result

        # Execute
        result = await incident_repo.bulk_update_status(
            incident_ids, IncidentStatus.RESOLVED
        )

        # Verify
        assert result == 3
        mock_session.commit.assert_called_once()


pytestmark = [pytest.mark.asyncio, pytest.mark.unit]
