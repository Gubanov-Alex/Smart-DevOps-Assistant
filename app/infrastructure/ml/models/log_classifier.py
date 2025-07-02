"""PyTorch-based log classification model."""

from typing import Any, Dict, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from app.infrastructure.ml.models.base import BaseMLModel


class LogClassifierNN(BaseMLModel):
    """
    Neural network for log message classification.

    Architecture: Embedding -> LSTM -> Dense -> Softmax
    Interview talking point: Real PyTorch implementation with proper architecture
    """

    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int = 128,
        hidden_dim: int = 64,
        num_layers: int = 2,
        dropout: float = 0.3,
        num_classes: int = 5,  # LogLevel enum count
    ):
        """Initialize the log classifier model."""
        super().__init__("LogClassifier", "1.0.0")

        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.num_classes = num_classes

        # Embedding layer
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)

        # LSTM layers
        self.lstm = nn.LSTM(
            embedding_dim,
            hidden_dim,
            num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=True,
        )

        # Attention mechanism
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_dim * 2,  # bidirectional
            num_heads=8,
            dropout=dropout,
            batch_first=True,
        )

        # Classification head
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, num_classes),
        )

        # Initialize weights
        self._init_weights()

    def _init_weights(self) -> None:
        """Initialize model weights using Xavier initialization."""
        for name, param in self.named_parameters():
            if "weight" in name and param.dim() > 1:
                nn.init.xavier_uniform_(param)
            elif "bias" in name:
                nn.init.constant_(param, 0.0)

    def forward(self, x: torch.Tensor, lengths: torch.Tensor = None) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input tensor [batch_size, seq_len]
            lengths: Sequence lengths for padding [batch_size]

        Returns:
            Class probabilities [batch_size, num_classes]
        """
        batch_size, seq_len = x.shape

        # Embedding
        embedded = self.embedding(x)  # [batch_size, seq_len, embedding_dim]

        # LSTM
        if lengths is not None:
            # Pack padded sequences for efficiency
            packed = nn.utils.rnn.pack_padded_sequence(
                embedded, lengths.cpu(), batch_first=True, enforce_sorted=False
            )
            lstm_out, (hidden, cell) = self.lstm(packed)
            lstm_out, _ = nn.utils.rnn.pad_packed_sequence(lstm_out, batch_first=True)
        else:
            lstm_out, (hidden, cell) = self.lstm(embedded)

        # Attention mechanism
        attended, attention_weights = self.attention(lstm_out, lstm_out, lstm_out)

        # Global max pooling over sequence dimension
        pooled = torch.max(attended, dim=1)[0]  # [batch_size, hidden_dim * 2]

        # Classification
        logits = self.classifier(pooled)  # [batch_size, num_classes]

        return logits

    def predict_proba(
        self, x: torch.Tensor, lengths: torch.Tensor = None
    ) -> torch.Tensor:
        """Get class probabilities."""
        self.eval()
        with torch.no_grad():
            logits = self.forward(x, lengths)
            probabilities = F.softmax(logits, dim=1)
        return probabilities

    def predict(
        self, x: torch.Tensor, lengths: torch.Tensor = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get predictions and confidence scores."""
        probabilities = self.predict_proba(x, lengths)
        predictions = torch.argmax(probabilities, dim=1)
        confidences = torch.max(probabilities, dim=1)[0]
        return predictions, confidences

    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed model information."""
        return {
            "model_name": self.model_name,
            "version": self.version,
            "architecture": "LSTM + Attention",
            "vocab_size": self.vocab_size,
            "embedding_dim": self.embedding_dim,
            "hidden_dim": self.hidden_dim,
            "num_layers": self.num_layers,
            "num_classes": self.num_classes,
            "parameter_count": self.get_parameter_count(),
            "is_trained": self.is_trained,
            "training_epochs": len(self.training_history),
        }
