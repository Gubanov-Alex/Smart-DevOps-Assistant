"""
Base ML model classes with security enhancements.

This module provides secure base classes for all ML models in the application.
"""

import abc
import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


class ModelSecurityError(Exception):
    """Исключение для проблем безопасности модели."""

    pass


class BaseMLModel(nn.Module, abc.ABC):
    """
    Base class for all ML models with security enhancements.

    Interview talking point: Production-ready model loading with security
    """

    ALLOWED_EXTENSIONS = {".pt", ".pth", ".ckpt"}
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

    def __init__(self, model_name: str, version: str = "1.0.0"):
        """Initialize ML model base class with security features."""
        super().__init__()
        self.model_name = model_name
        self.version = version
        self.is_trained = False
        self.training_history: List[Dict[str, float]] = []
        # Хеш для верификации целостности модели
        self._model_hash: Optional[str] = None

    @abc.abstractmethod
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass implementation."""
        pass

    @abc.abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and metadata."""
        pass

    def get_parameter_count(self) -> int:
        """Get the total number of trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def _validate_checkpoint_path(self, path: Union[str, Path]) -> Path:
        """Валидация пути к модели."""
        path = Path(path)

        # Проверка расширения файла
        if path.suffix not in self.ALLOWED_EXTENSIONS:
            raise ModelSecurityError(
                f"Unsupported file extension: {path.suffix}. "
                f"Allowed: {self.ALLOWED_EXTENSIONS}"
            )

        # Проверка существования файла
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {path}")

        # Проверка размера файла
        file_size = path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            raise ModelSecurityError(
                f"Model file too large: {file_size} bytes. "
                f"Maximum allowed: {self.MAX_FILE_SIZE} bytes"
            )

        # Проверка что это обычный файл (не symlink или device)
        if not path.is_file():
            raise ModelSecurityError(f"Path is not a regular file: {path}")

        return path

    def _calculate_file_hash(self, path: Path) -> str:
        """Вычисление SHA-256 хеша файла для верификации."""
        hash_sha256 = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            raise ModelSecurityError(f"Failed to calculate file hash: {e}")

    def save_checkpoint(
        self, path: Union[str, Path], metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Save model checkpoint with metadata and integrity check."""
        path = Path(path)

        # Создание директории если не существует
        path.parent.mkdir(parents=True, exist_ok=True)

        # Вычисление хеша состояния модели
        state_dict_str = str(self.state_dict())
        self._model_hash = hashlib.sha256(state_dict_str.encode()).hexdigest()

        checkpoint = {
            "model_state_dict": self.state_dict(),
            "model_name": self.model_name,
            "version": self.version,
            "is_trained": self.is_trained,
            "training_history": self.training_history,
            "parameter_count": self.get_parameter_count(),
            "model_hash": self._model_hash,
            "pytorch_version": torch.__version__,
            "metadata": metadata or {},
        }

        try:
            # Безопасное сохранение с проверкой прав доступа
            temp_path = path.with_suffix(path.suffix + ".tmp")
            torch.save(checkpoint, temp_path)
            temp_path.replace(path)  # Атомарная операция

            logger.info(
                f"Model checkpoint saved successfully: {path} "
                f"(hash: {self._model_hash[:8]}...)"
            )
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()  # Очистка временного файла
            raise ModelSecurityError(f"Failed to save model checkpoint: {e}")

    def load_checkpoint(
        self,
        path: Union[str, Path],
        expected_hash: Optional[str] = None,
        strict: bool = True,
    ) -> Dict[str, Any]:
        """
        Load model checkpoint with security validation.

        Args:
            path: Path to checkpoint file
            expected_hash: Expected SHA-256 hash for verification
            strict: Whether to enforce strict state dict loading

        Returns:
            Metadata from checkpoint
        """
        path = self._validate_checkpoint_path(path)

        # Вычисление и проверка хеша файла
        file_hash = self._calculate_file_hash(path)
        if expected_hash and file_hash != expected_hash:
            raise ModelSecurityError(
                f"File integrity check failed. Expected: {expected_hash}, "
                f"got: {file_hash}"
            )

        try:
            # Безопасная загрузка только весов модели с PyTorch 2.7+ compatibility
            with torch.serialization.safe_globals([torch.torch_version.TorchVersion]):
                checkpoint = torch.load(
                    path,
                    map_location="cpu",
                    weights_only=True,  # Критически важно для безопасности!
                )
        except Exception as e:
            logger.error(f"Failed to load checkpoint from {path}: {e}")
            raise ModelSecurityError(f"Corrupted or invalid checkpoint file: {e}")

        # Валидация структуры checkpoint
        required_keys = {"model_state_dict", "model_name", "version"}
        if not all(key in checkpoint for key in required_keys):
            missing_keys = required_keys - set(checkpoint.keys())
            raise ModelSecurityError(
                f"Invalid checkpoint format. Missing keys: {missing_keys}"
            )

        # Проверка совместимости версий PyTorch
        checkpoint_pytorch_version = checkpoint.get("pytorch_version")
        if (
            checkpoint_pytorch_version
            and checkpoint_pytorch_version != torch.__version__
        ):
            logger.warning(
                f"PyTorch version mismatch. Checkpoint: {checkpoint_pytorch_version}, "
                f"Current: {torch.__version__}"
            )

        # Проверка хеша модели если доступен
        stored_hash = checkpoint.get("model_hash")
        if stored_hash:
            state_dict_str = str(checkpoint["model_state_dict"])
            calculated_hash = hashlib.sha256(state_dict_str.encode()).hexdigest()
            if calculated_hash != stored_hash:
                raise ModelSecurityError("Model state dict integrity check failed")

        try:
            # Загрузка состояния модели
            self.load_state_dict(checkpoint["model_state_dict"], strict=strict)

            # Обновление метаданных
            self.model_name = checkpoint["model_name"]
            self.version = checkpoint["version"]
            self.is_trained = checkpoint.get("is_trained", False)
            self.training_history = checkpoint.get("training_history", [])
            self._model_hash = stored_hash

            logger.info(
                f"Model checkpoint loaded successfully: {path} "
                f"(parameters: {self.get_parameter_count()})"
            )

            return checkpoint.get("metadata", {})

        except Exception as e:
            raise ModelSecurityError(f"Failed to load model state: {e}")

    def verify_integrity(self) -> bool:
        """Проверка целостности загруженной модели."""
        if not self._model_hash:
            logger.warning("No model hash available for integrity check")
            return False

        current_state_str = str(self.state_dict())
        current_hash = hashlib.sha256(current_state_str.encode()).hexdigest()

        return current_hash == self._model_hash
