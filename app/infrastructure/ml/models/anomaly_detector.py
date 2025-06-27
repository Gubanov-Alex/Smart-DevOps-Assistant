"""PyTorch-based anomaly detection using autoencoder."""

from typing import Any, Dict, List, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from app.infrastructure.ml.models.base import BaseMLModel


class AutoEncoderAnomalyDetector(BaseMLModel):
    """
    Autoencoder for anomaly detection in time series metrics.

    Interview talking point: Unsupervised learning for anomaly detection
    """

    def __init__(
            self,
            input_dim: int,
            encoding_dim: int = 32,
            hidden_dims: List[int] = None,
            dropout: float = 0.2
    ):
        """Autoencoder for anomaly detection."""
        super().__init__("AnomalyDetector", "1.0.0")

        self.input_dim = input_dim
        self.encoding_dim = encoding_dim
        self.hidden_dims = hidden_dims or [64, 32]
        self.dropout = dropout

        # Build encoder
        encoder_layers = []
        prev_dim = input_dim

        for hidden_dim in self.hidden_dims:
            encoder_layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout)
            ])
            prev_dim = hidden_dim

        encoder_layers.append(nn.Linear(prev_dim, encoding_dim))
        self.encoder = nn.Sequential(*encoder_layers)

        # Build decoder (reverse of encoder)
        decoder_layers = []
        prev_dim = encoding_dim

        for hidden_dim in reversed(self.hidden_dims):
            decoder_layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout)
            ])
            prev_dim = hidden_dim

        decoder_layers.append(nn.Linear(prev_dim, input_dim))
        self.decoder = nn.Sequential(*decoder_layers)

        # Threshold for anomaly detection (learned during training)
        self.register_buffer('anomaly_threshold', torch.tensor(0.0))
        self.register_buffer('reconstruction_stats', torch.zeros(2))  # mean, std

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass through autoencoder.

        Args:
            x: Input tensor [batch_size, input_dim]

        Returns:
            (reconstructed, encoded) tensors
        """
        encoded = self.encoder(x)
        reconstructed = self.decoder(encoded)
        return reconstructed, encoded

    def reconstruction_error(self, x: torch.Tensor) -> torch.Tensor:
        """Calculate reconstruction error (MSE)."""
        reconstructed, _ = self.forward(x)
        mse = F.mse_loss(reconstructed, x, reduction='none')
        return torch.mean(mse, dim=1)  # [batch_size]

    def detect_anomalies(
            self,
            x: torch.Tensor,
            threshold_std_multiplier: float = 2.0
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Detect anomalies based on reconstruction error.

        Args:
            x: Input tensor [batch_size, input_dim]
            threshold_std_multiplier: Multiplier for a standard deviation threshold

        Returns:
            (anomaly_scores, is_anomaly) tensors
        """
        self.eval()
        with torch.no_grad():
            reconstruction_errors = self.reconstruction_error(x)

            # Calculate a threshold if not set
            if self.anomaly_threshold.item() == 0.0:
                threshold = reconstruction_errors.mean() + threshold_std_multiplier * reconstruction_errors.std()
            else:
                threshold = self.anomaly_threshold

            # Normalize scores to 0-1 range
            max_error = reconstruction_errors.max()
            min_error = reconstruction_errors.min()
            if max_error > min_error:
                anomaly_scores = (reconstruction_errors - min_error) / (max_error - min_error)
            else:
                anomaly_scores = torch.zeros_like(reconstruction_errors)

            is_anomaly = reconstruction_errors > threshold

        return anomaly_scores, is_anomaly

    def update_threshold(self, normal_data: torch.Tensor, std_multiplier: float = 2.0) -> None:
        """Update an anomaly threshold based on normal data statistics."""
        self.eval()
        with torch.no_grad():
            errors = self.reconstruction_error(normal_data)
            mean_error = errors.mean()
            std_error = errors.std()

            self.anomaly_threshold.copy_(mean_error + std_multiplier * std_error)
            self.reconstruction_stats.copy_(torch.tensor([mean_error.item(), std_error.item()]))

    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed model information."""
        return {
            "model_name": self.model_name,
            "version": self.version,
            "architecture": "Autoencoder",
            "input_dim": self.input_dim,
            "encoding_dim": self.encoding_dim,
            "hidden_dims": self.hidden_dims,
            "dropout": self.dropout,
            "parameter_count": self.get_parameter_count(),
            "anomaly_threshold": self.anomaly_threshold.item(),
            "reconstruction_stats": {
                "mean": self.reconstruction_stats[0].item(),
                "std": self.reconstruction_stats[1].item()
            },
            "is_trained": self.is_trained
        }
