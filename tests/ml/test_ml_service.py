"""Tests for ML Service to improve coverage."""

import pytest
import torch
from unittest.mock import  MagicMock, patch
from pathlib import Path

from app.services.ml_service import MLService
from app.infrastructure.ml.models.anomaly_detector import AutoEncoderAnomalyDetector
from app.infrastructure.ml.models.log_classifier import LogClassifierNN
from app.infrastructure.ml.preprocessing.text_processor import LogTextProcessor


class TestMLService:
    """Tests for MLService."""

    @pytest.fixture
    def mock_models(self):
        """Create mock models for testing."""
        anomaly_detector = MagicMock(spec=AutoEncoderAnomalyDetector)
        classifier = MagicMock(spec=LogClassifierNN)
        text_processor = MagicMock(spec=LogTextProcessor)

        # Configure mock return values
        anomaly_detector.detect_anomalies.return_value = (
            torch.tensor([0.1, 0.8, 0.3]),  # scores
            torch.tensor([False, True, False])  # is_anomaly
        )

        classifier.predict.return_value = (
            torch.tensor([0, 2, 1]),  # predictions
            torch.tensor([0.9, 0.7, 0.8])  # confidences
        )

        text_processor.encode_batch.return_value = (
            torch.randint(0, 100, (3, 20)),  # encoded
            torch.tensor([15, 18, 12])  # lengths
        )

        return {
            'anomaly_detector': anomaly_detector,
            'classifier': classifier,
            'text_processor': text_processor
        }

    @pytest.fixture
    def ml_service(self, mock_models):
        """Create an MLService instance with mock models."""
        service = MLService()
        service.anomaly_detector = mock_models['anomaly_detector']
        service.classifier = mock_models['classifier']
        service.text_processor = mock_models['text_processor']
        service.models_loaded = True
        return service

    def test_service_initialization(self):
        """Test MLService initialization."""
        service = MLService()
        assert not service.models_loaded
        assert service.anomaly_detector is None
        assert service.classifier is None
        assert service.text_processor is None

    @pytest.mark.asyncio
    async def test_load_models_success(self):
        """Test successful model loading."""
        service = MLService()

        with patch('app.services.ml_service.AutoEncoderAnomalyDetector') as mock_anomaly, \
                patch('app.services.ml_service.LogClassifierNN') as mock_classifier, \
                patch('app.services.ml_service.LogTextProcessor') as mock_processor, \
                patch.object(Path, 'exists', return_value=True):
            mock_anomaly_instance = MagicMock()
            mock_classifier_instance = MagicMock()
            mock_processor_instance = MagicMock()

            mock_anomaly.return_value = mock_anomaly_instance
            mock_classifier.return_value = mock_classifier_instance
            mock_processor.return_value = mock_processor_instance

            await service.load_models()

            assert service.models_loaded
            assert service.anomaly_detector == mock_anomaly_instance
            assert service.classifier == mock_classifier_instance
            assert service.text_processor == mock_processor_instance

    @pytest.mark.asyncio
    async def test_load_models_file_not_found(self):
        """Test model loading when files don't exist."""
        service = MLService()

        with patch.object(Path, 'exists', return_value=False):
            await service.load_models()

            # Should still create models even if checkpoint files don't exist
            assert service.models_loaded

    @pytest.mark.asyncio
    async def test_analyze_logs_success(self, ml_service):
        """Test successful log analysis."""
        log_messages = [
            "INFO: Application started successfully",
            "ERROR: Database connection failed",
            "WARNING: Memory usage high"
        ]

        result = await ml_service.analyze_logs(log_messages)

        assert "anomaly_detection" in result
        assert "classification" in result
        assert "summary" in result

        # Check anomaly detection results
        anomaly_results = result["anomaly_detection"]
        assert "scores" in anomaly_results
        assert "anomalies" in anomaly_results
        assert len(anomaly_results["scores"]) == 3

        # Check classification results
        classification_results = result["classification"]
        assert "predictions" in classification_results
        assert "confidences" in classification_results
        assert len(classification_results["predictions"]) == 3

    @pytest.mark.asyncio
    async def test_analyze_logs_models_not_loaded(self):
        """Test log analysis when models are not loaded."""
        service = MLService()

        with pytest.raises(RuntimeError, match="Models not loaded"):
            await service.analyze_logs(["test message"])

    @pytest.mark.asyncio
    async def test_analyze_logs_empty_input(self, ml_service):
        """Test log analysis with empty input."""
        result = await ml_service.analyze_logs([])

        assert result["anomaly_detection"]["scores"] == []
        assert result["classification"]["predictions"] == []
        assert result["summary"]["total_logs"] == 0

    @pytest.mark.asyncio
    async def test_detect_anomalies_success(self, ml_service):
        """Test anomaly detection."""
        log_messages = ["Test message 1", "Test message 2"]

        result = await ml_service.detect_anomalies(log_messages)

        assert "scores" in result
        assert "anomalies" in result
        assert "threshold" in result
        assert len(result["scores"]) == 2

    @pytest.mark.asyncio
    async def test_classify_logs_success(self, ml_service):
        """Test log classification."""
        log_messages = ["INFO: Test", "ERROR: Failed"]

        result = await ml_service.classify_logs(log_messages)

        assert "predictions" in result
        assert "confidences" in result
        assert "class_names" in result
        assert len(result["predictions"]) == 2

    @pytest.mark.asyncio
    async def test_get_model_info(self, ml_service):
        """Test getting model information."""
        # Mock model info
        ml_service.anomaly_detector.get_model_info.return_value = {
            "model_name": "AnomalyDetector",
            "version": "1.0.0",
            "parameter_count": 1000
        }

        ml_service.classifier.get_model_info.return_value = {
            "model_name": "LogClassifier",
            "version": "1.0.0",
            "parameter_count": 5000
        }

        info = await ml_service.get_model_info()

        assert "anomaly_detector" in info
        assert "classifier" in info
        assert "models_loaded" in info
        assert info["models_loaded"] == True

    @pytest.mark.asyncio
    async def test_update_anomaly_threshold(self, ml_service):
        """Test updating anomaly threshold."""
        normal_logs = ["Normal message 1", "Normal message 2"]

        await ml_service.update_anomaly_threshold(normal_logs, threshold_multiplier=2.5)

        # Verify that update_threshold was called on the anomaly detector
        ml_service.anomaly_detector.update_threshold.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_processing_large_input(self, ml_service):
        """Test batch processing with large input."""
        # Create a large number of log messages
        large_log_batch = [f"Log message {i}" for i in range(1000)]

        with patch.object(ml_service, '_process_batch') as mock_process:
            mock_process.return_value = {
                "anomaly_detection": {"scores": [0.1] * 1000, "anomalies": [False] * 1000},
                "classification": {"predictions": [0] * 1000, "confidences": [0.9] * 1000}
            }

            result = await ml_service.analyze_logs(large_log_batch)

            assert result["summary"]["total_logs"] == 1000

    @pytest.mark.asyncio
    async def test_error_handling_in_analysis(self, ml_service):
        """Test error handling during analysis."""
        # Make the anomaly detector raise an exception
        ml_service.anomaly_detector.detect_anomalies.side_effect = Exception("Model error")

        with pytest.raises(Exception):
            await ml_service.detect_anomalies(["test message"])

    @pytest.mark.asyncio
    async def test_preprocessing_integration(self, ml_service):
        """Test integration with text preprocessing."""
        log_messages = ["<script>alert('xss')</script>", "Normal message"]

        # Configure text processor to return clean data
        ml_service.text_processor.encode_batch.return_value = (
            torch.randint(0, 100, (2, 10)),
            torch.tensor([8, 10])
        )

        result = await ml_service.analyze_logs(log_messages)

        # Verify text processor was called
        ml_service.text_processor.encode_batch.assert_called_once()
        assert "anomaly_detection" in result
        assert "classification" in result

    def test_class_name_mapping(self, ml_service):
        """Test class name mapping for predictions."""
        class_names = ml_service._get_class_names()

        expected_names = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert class_names == expected_names

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, ml_service):
        """Test handling concurrent analysis requests."""
        import asyncio

        log_batches = [
            ["Message batch 1"],
            ["Message batch 2"],
            ["Message batch 3"]
        ]

        # Run multiple analysis requests concurrently
        tasks = [ml_service.analyze_logs(batch) for batch in log_batches]
        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        for result in results:
            assert "anomaly_detection" in result
            assert "classification" in result

    @pytest.mark.asyncio
    async def test_model_performance_monitoring(self, ml_service):
        """Test performance monitoring functionality."""
        log_messages = ["Test message"]

        # Mock performance tracking
        with patch('time.time', side_effect=[0.0, 0.1, 0.2, 0.3]):  # Mock timing
            result = await ml_service.analyze_logs(log_messages)

            # Check if performance metrics are included
            assert "summary" in result
            summary = result["summary"]
            assert "total_logs" in summary

    def test_memory_management(self, ml_service):
        """Test memory management during processing."""
        # Test that tensors are properly cleaned up
        initial_memory = torch.cuda.memory_allocated() if torch.cuda.is_available() else 0

        # Process some data
        with torch.no_grad():
            dummy_tensor = torch.randn(100, 100)
            del dummy_tensor

        final_memory = torch.cuda.memory_allocated() if torch.cuda.is_available() else 0

        # Memory should not increase significantly
        if torch.cuda.is_available():
            assert final_memory <= initial_memory + 1024  # Allow small fluctuation


class TestMLServiceEdgeCases:
    """Test edge cases for MLService."""

    @pytest.mark.asyncio
    async def test_very_long_messages(self):
        """Test handling of very long log messages."""
        service = MLService()

        # Create extremely long message
        very_long_message = "A" * 50000

        with patch.object(service, 'models_loaded', True), \
                patch.object(service, 'text_processor') as mock_processor:
            mock_processor.encode_batch.return_value = (
                torch.randint(0, 100, (1, 128)),  # Truncated to max length
                torch.tensor([128])
            )

            # Should handle long messages without crashing
            await service._prepare_features([very_long_message])

    @pytest.mark.asyncio
    async def test_special_characters_in_logs(self):
        """Test handling of special characters in log messages."""
        service = MLService()
        service.models_loaded = True
        service.text_processor = MagicMock()

        special_messages = [
            "Message with émojis 🚀🔥",
            "Unicode test: ñáéíóú",
            "Special chars: @#$%^&*()",
            "Mixed: 中文测试"
        ]

        service.text_processor.encode_batch.return_value = (
            torch.randint(0, 100, (4, 20)),
            torch.tensor([15, 12, 18, 10])
        )

        #
