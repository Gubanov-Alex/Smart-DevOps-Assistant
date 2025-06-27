"""Comprehensive tests for ML models to improve coverage."""

import torch

from app.infrastructure.ml.models.anomaly_detector import AutoEncoderAnomalyDetector
from app.infrastructure.ml.models.log_classifier import LogClassifierNN


class TestAutoEncoderAnomalyDetector:
    """Tests for AutoEncoderAnomalyDetector."""

    def test_model_initialization(self):
        """Test model initialization with different parameters."""
        model = AutoEncoderAnomalyDetector(input_dim=10)
        assert model.input_dim == 10
        assert model.encoding_dim == 32
        assert model.model_name == "AnomalyDetector"
        assert model.version == "1.0.0"

    def test_model_with_custom_parameters(self):
        """Test model with custom parameters."""
        model = AutoEncoderAnomalyDetector(
            input_dim=20, encoding_dim=16, hidden_dims=[64, 32, 16], dropout=0.3
        )
        assert model.input_dim == 20
        assert model.encoding_dim == 16
        assert model.hidden_dims == [64, 32, 16]
        assert model.dropout == 0.3

    def test_forward_pass(self):
        """Test forward pass through the model."""
        model = AutoEncoderAnomalyDetector(input_dim=10)
        model.eval()

        # Create sample input
        x = torch.randn(5, 10)  # batch_size=5, input_dim=10

        with torch.no_grad():
            reconstructed, encoded = model.forward(x)

        assert reconstructed.shape == (5, 10)
        assert encoded.shape == (5, 32)  # encoding_dim=32

    def test_reconstruction_error(self):
        """Test reconstruction error calculation."""
        model = AutoEncoderAnomalyDetector(input_dim=10)
        model.eval()

        x = torch.randn(3, 10)

        with torch.no_grad():
            error = model.reconstruction_error(x)

        assert error.shape == (3,)  # One error per sample
        assert torch.all(error >= 0)  # Errors should be non-negative

    def test_detect_anomalies(self):
        """Test anomaly detection functionality."""
        model = AutoEncoderAnomalyDetector(input_dim=10)
        model.eval()

        x = torch.randn(4, 10)

        with torch.no_grad():
            scores, is_anomaly = model.detect_anomalies(x)

        assert scores.shape == (4,)
        assert is_anomaly.shape == (4,)
        assert torch.all((scores >= 0) & (scores <= 1))  # Scores in [0,1]
        assert is_anomaly.dtype == torch.bool

    def test_update_threshold(self):
        """Test threshold update functionality."""
        model = AutoEncoderAnomalyDetector(input_dim=10)
        model.eval()

        # Generate normal data
        normal_data = torch.randn(20, 10)

        # Initial threshold should be 0
        assert model.anomaly_threshold.item() == 0.0

        model.update_threshold(normal_data, std_multiplier=2.0)

        # Threshold should be updated
        assert model.anomaly_threshold.item() > 0.0
        assert len(model.reconstruction_stats) == 2  # mean and std

    def test_get_model_info(self):
        """Test model info retrieval."""
        model = AutoEncoderAnomalyDetector(
            input_dim=15, encoding_dim=8, hidden_dims=[32, 16], dropout=0.25
        )

        info = model.get_model_info()

        assert info["model_name"] == "AnomalyDetector"
        assert info["version"] == "1.0.0"
        assert info["architecture"] == "Autoencoder"
        assert info["input_dim"] == 15
        assert info["encoding_dim"] == 8
        assert info["hidden_dims"] == [32, 16]
        assert info["dropout"] == 0.25
        assert "parameter_count" in info
        assert "anomaly_threshold" in info
        assert "reconstruction_stats" in info

    def test_parameter_count(self):
        """Test parameter counting."""
        model = AutoEncoderAnomalyDetector(input_dim=10, encoding_dim=5)
        param_count = model.get_parameter_count()
        assert param_count > 0
        assert isinstance(param_count, int)


class TestLogClassifierNN:
    """Tests for LogClassifierNN."""

    def test_model_initialization(self):
        """Test model initialization."""
        model = LogClassifierNN(vocab_size=1000)
        assert model.vocab_size == 1000
        assert model.embedding_dim == 128
        assert model.hidden_dim == 64
        assert model.num_layers == 2
        assert model.num_classes == 5
        assert model.model_name == "LogClassifier"

    def test_model_with_custom_parameters(self):
        """Test model with custom parameters."""
        model = LogClassifierNN(
            vocab_size=5000,
            embedding_dim=256,
            hidden_dim=128,
            num_layers=3,
            dropout=0.4,
            num_classes=10,
        )
        assert model.vocab_size == 5000
        assert model.embedding_dim == 256
        assert model.hidden_dim == 128
        assert model.num_layers == 3
        assert model.num_classes == 10

    def test_forward_pass(self):
        """Test forward pass through the model."""
        model = LogClassifierNN(vocab_size=1000, num_classes=5)
        model.eval()

        # Create sample input (token indices)
        x = torch.randint(0, 1000, (3, 20))  # batch_size=3, seq_len=20

        with torch.no_grad():
            logits = model.forward(x)

        assert logits.shape == (3, 5)  # batch_size, num_classes

    def test_forward_with_lengths(self):
        """Test forward pass with sequence lengths."""
        model = LogClassifierNN(vocab_size=1000, num_classes=5)
        model.eval()

        x = torch.randint(0, 1000, (2, 15))
        lengths = torch.tensor([10, 12])  # Actual sequence lengths

        with torch.no_grad():
            logits = model.forward(x, lengths)

        assert logits.shape == (2, 5)

    def test_predict_proba(self):
        """Test probability prediction."""
        model = LogClassifierNN(vocab_size=1000, num_classes=5)
        model.eval()

        x = torch.randint(0, 1000, (2, 10))

        probabilities = model.predict_proba(x)

        assert probabilities.shape == (2, 5)
        # Check that probabilities sum to 1
        assert torch.allclose(probabilities.sum(dim=1), torch.ones(2), atol=1e-5)
        assert torch.all((probabilities >= 0) & (probabilities <= 1))

    def test_predict(self):
        """Test prediction with confidence."""
        model = LogClassifierNN(vocab_size=1000, num_classes=5)
        model.eval()

        x = torch.randint(0, 1000, (3, 10))

        predictions, confidences = model.predict(x)

        assert predictions.shape == (3,)
        assert confidences.shape == (3,)
        assert torch.all((predictions >= 0) & (predictions < 5))  # Valid class indices
        assert torch.all((confidences >= 0) & (confidences <= 1))  # Valid confidences

    def test_get_model_info(self):
        """Test model info retrieval."""
        model = LogClassifierNN(
            vocab_size=2000,
            embedding_dim=64,
            hidden_dim=32,
            num_layers=1,
            num_classes=3,
        )

        info = model.get_model_info()

        assert info["model_name"] == "LogClassifier"
        assert info["version"] == "1.0.0"
        assert info["architecture"] == "LSTM + Attention"
        assert info["vocab_size"] == 2000
        assert info["embedding_dim"] == 64
        assert info["hidden_dim"] == 32
        assert info["num_layers"] == 1
        assert info["num_classes"] == 3
        assert "parameter_count" in info
        assert "training_epochs" in info

    def test_weights_initialization(self):
        """Test that weights are properly initialized."""
        model = LogClassifierNN(vocab_size=100, num_classes=3)

        # Check that weights are not all zeros
        embedding_weights = model.embedding.weight
        assert not torch.all(embedding_weights == 0)

        # Check LSTM weights
        for name, param in model.lstm.named_parameters():
            if "weight" in name:
                assert not torch.all(param == 0)

    def test_parameter_count(self):
        """Test parameter counting."""
        model = LogClassifierNN(vocab_size=1000, num_classes=5)
        param_count = model.get_parameter_count()
        assert param_count > 0
        assert isinstance(param_count, int)

    def test_model_training_mode(self):
        """Test switching between training and evaluation modes."""
        model = LogClassifierNN(vocab_size=100, num_classes=3)

        # Test training mode
        model.train()
        assert model.training

        # Test evaluation mode
        model.eval()
        assert not model.training

    def test_gradient_flow(self):
        """Test that gradients flow through the model."""
        model = LogClassifierNN(vocab_size=100, num_classes=3)
        model.train()

        x = torch.randint(0, 100, (2, 10))
        target = torch.tensor([0, 1])

        # Forward pass
        logits = model.forward(x)
        loss = torch.nn.functional.cross_entropy(logits, target)

        # Backward pass
        loss.backward()

        # Check that some gradients are non-zero
        has_grad = False
        for param in model.parameters():
            if param.grad is not None and torch.any(param.grad != 0):
                has_grad = True
                break

        assert has_grad, "No gradients found in the model"


class TestModelIntegration:
    """Integration tests for ML models."""

    def test_models_can_be_used_together(self):
        """Test that both models can be instantiated and used together."""
        # Create both models
        anomaly_detector = AutoEncoderAnomalyDetector(input_dim=50)
        classifier = LogClassifierNN(vocab_size=1000, num_classes=5)

        # Test anomaly detector
        features = torch.randn(3, 50)
        scores, anomalies = anomaly_detector.detect_anomalies(features)

        # Test classifier
        tokens = torch.randint(0, 1000, (3, 20))
        predictions, confidences = classifier.predict(tokens)

        assert scores.shape == (3,)
        assert predictions.shape == (3,)
        assert len(anomalies) == 3
        assert len(confidences) == 3

    def test_models_info_completeness(self):
        """Test that model info is complete for both models."""
        anomaly_detector = AutoEncoderAnomalyDetector(input_dim=10)
        classifier = LogClassifierNN(vocab_size=100)

        anomaly_info = anomaly_detector.get_model_info()
        classifier_info = classifier.get_model_info()

        # Check required fields
        required_fields = ["model_name", "version", "parameter_count", "is_trained"]

        for field in required_fields:
            assert field in anomaly_info, f"Missing {field} in anomaly detector info"
            assert field in classifier_info, f"Missing {field} in classifier info"

    def test_model_memory_efficiency(self):
        """Test that models don't use excessive memory."""
        # Create models with reasonable sizes
        anomaly_detector = AutoEncoderAnomalyDetector(input_dim=100, encoding_dim=20)
        classifier = LogClassifierNN(vocab_size=5000, embedding_dim=64, hidden_dim=32)

        # Get parameter counts
        anomaly_params = anomaly_detector.get_parameter_count()
        classifier_params = classifier.get_parameter_count()

        # Check that parameter counts are reasonable (not excessively large)
        assert (
            anomaly_params < 1_000_000
        ), f"Anomaly detector too large: {anomaly_params} params"
        assert (
            classifier_params < 5_000_000
        ), f"Classifier too large: {classifier_params} params"
