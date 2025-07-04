"""Tests for MLModelRepository implementation - simplified version matching domain entity."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import MLModel as MLModelEntity
from app.domain.entities import (
    ModelStatus,
)
from app.infrastructure.repositories.mlmodel_repository import (
    MLModelRepository,
    RepositoryError,
)
from app.models import MLModel as MLModelModel

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
def sample_model():
    """Create sample ML model entity for testing - matching domain entity structure."""
    return MLModelEntity(
        name=fake.word(),
        model_type="classifier",
        version="1.0.0",
        id=uuid4(),
        status=ModelStatus.TRAINED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        deployed_at=None,
        accuracy=0.95,
        training_duration_minutes=120,
        model_path=f"/models/{fake.word()}.pkl",
        config={"param1": "value1"},
        metrics={"f1_score": 0.94, "precision": 0.93, "recall": 0.92},
        metadata={"test": "metadata"},
    )


@pytest.fixture
def mlmodel_repo(mock_session):
    """Create ML model repository with mock session."""
    return MLModelRepository(mock_session)


class TestMLModelRepository:
    """Test suite for MLModelRepository."""

    @pytest.mark.asyncio
    async def test_save_new_model(self, mlmodel_repo, mock_session, sample_model):
        """Test saving a new ML model."""
        # Setup
        with patch.object(mlmodel_repo, "find_by_name_and_version", return_value=None):
            # Execute
            await mlmodel_repo.save(sample_model)

        # Verify
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_existing_model(self, mlmodel_repo, mock_session, sample_model):
        """Test updating existing model."""
        # Setup
        existing_model = MagicMock(spec=MLModelModel)
        mock_session.get.return_value = existing_model

        with patch.object(
            mlmodel_repo, "find_by_name_and_version", return_value=sample_model
        ):
            # Execute
            await mlmodel_repo.save(sample_model)

        # Verify
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_name_and_version(
        self, mlmodel_repo, mock_session, sample_model
    ):
        """Test finding model by name and version."""
        # Setup
        mock_result = MagicMock()
        mock_model = MagicMock(spec=MLModelModel)
        mock_model.id = sample_model.id
        mock_model.name = sample_model.name
        mock_model.version = sample_model.version
        mock_model.model_type = sample_model.model_type
        mock_model.status = sample_model.status.value
        mock_model.created_at = sample_model.created_at
        mock_model.updated_at = sample_model.updated_at
        mock_model.trained_at = None  # Not in domain entity
        mock_model.deployed_at = sample_model.deployed_at
        mock_model.accuracy = sample_model.accuracy
        mock_model.precision = sample_model.metrics.get("precision")
        mock_model.recall = sample_model.metrics.get("recall")
        mock_model.f1_score = sample_model.metrics.get("f1_score")
        mock_model.training_dataset_size = None  # Not in domain entity
        mock_model.training_duration_minutes = sample_model.training_duration_minutes
        mock_model.model_path = sample_model.model_path
        mock_model.config = sample_model.config
        mock_model.extra_data = sample_model.metadata
        mock_model.is_active = True  # Default
        mock_model.deployment_config = {}  # Default

        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        # Execute
        result = await mlmodel_repo.find_by_name_and_version(
            sample_model.name, sample_model.version
        )

        # Verify
        assert result is not None
        assert result.name == sample_model.name
        assert result.version == sample_model.version

    @pytest.mark.asyncio
    async def test_find_by_name_and_version_not_found(self, mlmodel_repo, mock_session):
        """Test finding non-existent model."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Execute
        result = await mlmodel_repo.find_by_name_and_version("nonexistent", "1.0.0")

        # Verify
        assert result is None

    @pytest.mark.asyncio
    async def test_find_latest_ready(self, mlmodel_repo, mock_session):
        """Test finding latest ready model."""
        # Setup
        mock_result = MagicMock()
        mock_model = MagicMock(spec=MLModelModel)
        mock_model.id = uuid4()
        mock_model.name = "test_model"
        mock_model.version = "2.0.0"
        mock_model.model_type = "classifier"
        mock_model.status = ModelStatus.DEPLOYED.value
        mock_model.created_at = datetime.now(timezone.utc)
        mock_model.updated_at = datetime.now(timezone.utc)
        mock_model.trained_at = None
        mock_model.deployed_at = datetime.now(timezone.utc)
        mock_model.accuracy = 0.96
        mock_model.precision = 0.95
        mock_model.recall = 0.94
        mock_model.f1_score = 0.95
        mock_model.training_dataset_size = 15000
        mock_model.training_duration_minutes = 180
        mock_model.model_path = "/models/latest.pkl"
        mock_model.config = {}
        mock_model.extra_data = {}
        mock_model.is_active = True
        mock_model.deployment_config = {}

        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        # Execute
        result = await mlmodel_repo.find_latest_ready("classifier")

        # Verify
        assert result is not None
        assert result.model_type == "classifier"
        assert result.status == ModelStatus.DEPLOYED

    @pytest.mark.asyncio
    async def test_get_active_models(self, mlmodel_repo, mock_session):
        """Test getting active models."""
        # Setup
        mock_result = MagicMock()
        mock_models = []
        for i in range(2):
            model = MagicMock(spec=MLModelModel)
            model.id = uuid4()
            model.name = f"model_{i}"
            model.version = f"{i + 1}.0.0"
            model.model_type = "classifier"
            model.status = ModelStatus.DEPLOYED.value
            model.created_at = datetime.now(timezone.utc)
            model.updated_at = datetime.now(timezone.utc)
            model.trained_at = None
            model.deployed_at = datetime.now(timezone.utc)
            model.accuracy = 0.9 + i * 0.01
            model.precision = 0.9 + i * 0.01
            model.recall = 0.9 + i * 0.01
            model.f1_score = 0.9 + i * 0.01
            model.training_dataset_size = 10000
            model.training_duration_minutes = 120
            model.model_path = f"/models/model_{i}.pkl"
            model.config = {}
            model.extra_data = {}
            model.is_active = True
            model.deployment_config = {}
            mock_models.append(model)

        mock_result.scalars.return_value.all.return_value = mock_models
        mock_session.execute.return_value = mock_result

        # Execute
        result = await mlmodel_repo.get_active_models()

        # Verify
        assert len(result) == 2
        assert all(model.is_deployed for model in result)

    @pytest.mark.asyncio
    async def test_update_status(self, mlmodel_repo, mock_session):
        """Test updating model status."""
        # Setup
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result
        mock_session.get.return_value = None

        # Execute
        result = await mlmodel_repo.update_status(
            uuid4(), ModelStatus.DEPLOYED, {"deployment_notes": "Success"}
        )

        # Verify
        assert result is True
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling(self, mlmodel_repo, mock_session, sample_model):
        """Test error handling."""
        # Setup
        mock_session.execute.side_effect = Exception("DB Error")

        # Execute & Verify
        with pytest.raises(RepositoryError):
            await mlmodel_repo.find_by_name_and_version("test", "1.0.0")

    @pytest.mark.asyncio
    async def test_find_all_versions(self, mlmodel_repo, mock_session):
        """Test finding all versions of a model."""
        # Setup
        mock_result = MagicMock()
        model_versions = []
        for i in range(3):
            version_model = MagicMock(spec=MLModelModel)
            version_model.id = uuid4()
            version_model.name = "sentiment_classifier"
            version_model.version = f"{i + 1}.0.0"
            version_model.model_type = "classifier"
            version_model.status = ModelStatus.TRAINED.value
            version_model.created_at = datetime.now(timezone.utc) - timedelta(days=i)
            version_model.updated_at = datetime.now(timezone.utc)
            version_model.trained_at = None
            version_model.deployed_at = None
            version_model.accuracy = 0.85 + i * 0.02
            version_model.precision = 0.84 + i * 0.02
            version_model.recall = 0.83 + i * 0.02
            version_model.f1_score = 0.84 + i * 0.02
            version_model.training_dataset_size = 10000
            version_model.training_duration_minutes = 60
            version_model.model_path = f"/models/v{i + 1}.pkl"
            version_model.config = {}
            version_model.extra_data = {}
            version_model.is_active = True
            version_model.deployment_config = {}
            model_versions.append(version_model)

        mock_result.scalars.return_value.all.return_value = model_versions
        mock_session.execute.return_value = mock_result

        # Execute
        result = await mlmodel_repo.find_all_versions("sentiment_classifier")

        # Verify
        assert len(result) == 3
        assert all(model.name == "sentiment_classifier" for model in result)

    @pytest.mark.asyncio
    async def test_get_by_id(self, mlmodel_repo, mock_session):
        """Test getting model by ID."""
        # Setup
        model_id = uuid4()
        mock_model = MagicMock(spec=MLModelModel)
        mock_model.id = model_id
        mock_model.name = "fraud_detector"
        mock_model.version = "2.1.0"
        mock_model.model_type = "classifier"
        mock_model.status = ModelStatus.DEPLOYED.value
        mock_model.created_at = datetime.now(timezone.utc)
        mock_model.updated_at = datetime.now(timezone.utc)
        mock_model.trained_at = None
        mock_model.deployed_at = datetime.now(timezone.utc)
        mock_model.accuracy = 0.92
        mock_model.precision = 0.91
        mock_model.recall = 0.90
        mock_model.f1_score = 0.91
        mock_model.training_dataset_size = 50000
        mock_model.training_duration_minutes = 180
        mock_model.model_path = "/models/fraud_v2.pkl"
        mock_model.config = {"threshold": 0.7}
        mock_model.extra_data = {"validation_notes": "Excellent performance"}
        mock_model.is_active = True
        mock_model.deployment_config = {"replicas": 3}

        mock_session.get.return_value = mock_model

        # Execute
        result = await mlmodel_repo.get_by_id(model_id)

        # Verify
        assert result is not None
        assert result.id == model_id
        assert result.name == "fraud_detector"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, mlmodel_repo, mock_session):
        """Test getting non-existent model by ID."""
        # Setup
        mock_session.get.return_value = None

        # Execute
        result = await mlmodel_repo.get_by_id(uuid4())

        # Verify
        assert result is None

    @pytest.mark.asyncio
    async def test_deactivate_model(self, mlmodel_repo, mock_session):
        """Test deactivating a model."""
        # Setup
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        # Execute
        result = await mlmodel_repo.deactivate_model(uuid4())

        # Verify
        assert result is True
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_models_by_performance(self, mlmodel_repo, mock_session):
        """Test finding models by performance criteria."""
        # Setup
        mock_result = MagicMock()
        high_perf_model = MagicMock(spec=MLModelModel)
        high_perf_model.id = uuid4()
        high_perf_model.name = "high_performance_model"
        high_perf_model.version = "1.0.0"
        high_perf_model.model_type = "regressor"
        high_perf_model.status = ModelStatus.DEPLOYED.value
        high_perf_model.created_at = datetime.now(timezone.utc)
        high_perf_model.updated_at = datetime.now(timezone.utc)
        high_perf_model.trained_at = None
        high_perf_model.deployed_at = datetime.now(timezone.utc)
        high_perf_model.accuracy = 0.95
        high_perf_model.precision = 0.94
        high_perf_model.recall = 0.93
        high_perf_model.f1_score = 0.94
        high_perf_model.training_dataset_size = 100000
        high_perf_model.training_duration_minutes = 300
        high_perf_model.model_path = "/models/high_perf.pkl"
        high_perf_model.config = {}
        high_perf_model.extra_data = {}
        high_perf_model.is_active = True
        high_perf_model.deployment_config = {}

        mock_result.scalars.return_value.all.return_value = [high_perf_model]
        mock_session.execute.return_value = mock_result

        # Execute
        result = await mlmodel_repo.find_models_by_performance(
            model_type="regressor", min_accuracy=0.90, min_f1_score=0.90, limit=5
        )

        # Verify
        assert len(result) == 1
        assert result[0].accuracy >= 0.90
        assert result[0].metrics["f1_score"] >= 0.90

    @pytest.mark.asyncio
    async def test_get_model_statistics(self, mlmodel_repo, mock_session):
        """Test getting model statistics."""
        # Setup
        # Mock status counts
        status_result = MagicMock()
        status_rows = [
            MagicMock(status="TRAINED", count=5),
            MagicMock(status="DEPLOYED", count=2),
            MagicMock(status="TRAINING", count=1),
        ]
        status_result.__iter__ = lambda self: iter(status_rows)

        # Mock type counts
        type_result = MagicMock()
        type_rows = [
            MagicMock(model_type="classifier", count=4),
            MagicMock(model_type="regressor", count=3),
            MagicMock(model_type="clustering", count=1),
        ]
        type_result.__iter__ = lambda self: iter(type_rows)

        # Mock performance metrics
        perf_result = MagicMock()
        perf_row = MagicMock()
        perf_row.avg_accuracy = 0.89
        perf_row.avg_f1_score = 0.87
        perf_row.avg_training_time = 120.5
        perf_result.first.return_value = perf_row

        mock_session.execute.side_effect = [status_result, type_result, perf_result]

        # Execute
        result = await mlmodel_repo.get_model_statistics()

        # Verify
        assert result["total_active_models"] == 8  # 5+2+1
        assert result["by_status"]["TRAINED"] == 5
        assert result["by_type"]["classifier"] == 4
        assert result["performance_metrics"]["average_accuracy"] == 0.89

    @pytest.mark.asyncio
    async def test_cleanup_old_versions(self, mlmodel_repo, mock_session):
        """Test cleaning up old model versions."""
        # Setup
        # Mock keep IDs query
        keep_result = MagicMock()
        keep_rows = [MagicMock(id=uuid4()) for _ in range(3)]
        keep_result.__iter__ = lambda self: iter(keep_rows)

        # Mock cleanup update result
        cleanup_result = MagicMock()
        cleanup_result.rowcount = 5

        mock_session.execute.side_effect = [keep_result, cleanup_result]

        # Execute
        result = await mlmodel_repo.cleanup_old_versions("old_model", keep_versions=3)

        # Verify
        assert result == 5
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_promote_to_production(self, mlmodel_repo, mock_session):
        """Test promoting model to production."""
        # Setup
        model_id = uuid4()
        mock_model = MagicMock(spec=MLModelModel)
        mock_model.model_type = "classifier"
        mock_session.get.return_value = mock_model

        # Mock demote and promote results
        demote_result = MagicMock()
        demote_result.rowcount = 1
        promote_result = MagicMock()
        promote_result.rowcount = 1

        mock_session.execute.side_effect = [demote_result, promote_result]

        # Execute
        result = await mlmodel_repo.promote_to_production(model_id)

        # Verify
        assert result is True
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_promote_to_production_model_not_found(
        self, mlmodel_repo, mock_session
    ):
        """Test promoting non-existent model."""
        # Setup
        mock_session.get.return_value = None

        # Execute & Verify
        with pytest.raises(RepositoryError, match="Model .* not found"):
            await mlmodel_repo.promote_to_production(uuid4())


pytestmark = [pytest.mark.asyncio, pytest.mark.unit]
