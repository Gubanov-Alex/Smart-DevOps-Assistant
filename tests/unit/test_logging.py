"""Тесты для модуля логирования."""

import logging
from unittest.mock import MagicMock, patch

import pytest
import structlog

from app.core.logging import add_app_context, get_logger, log_request_response, setup_logging


class TestLogging:
    """Тесты для проверки функций логирования."""

    def test_add_app_context(self):
        """Проверка добавления контекста приложения в логи."""
        logger = MagicMock()
        method_name = "info"
        event_dict = {"message": "test"}

        result = add_app_context(logger, method_name, event_dict)

        assert result["app"] == "smart-devops-assistant"
        assert result["version"] == "0.1.0"
        assert result["message"] == "test"

    def test_get_logger(self):
        """Проверка получения логгера."""
        with patch("structlog.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            logger = get_logger("test_logger")

            mock_get_logger.assert_called_once_with("test_logger")
            assert logger == mock_logger

    @patch("structlog.get_logger")
    def test_log_request_response(self, mock_get_logger):
        """Проверка логирования HTTP запросов и ответов."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        log_request_response(
            method="GET",
            url="/api/v1/resource",
            status_code=200,
            duration=0.5,
            extra={"user_id": "123"},
        )

        mock_get_logger.assert_called_once_with("http")
        mock_logger.info.assert_called_once()

        # Проверяем аргументы вызова
        args, kwargs = mock_logger.info.call_args
        assert args[0] == "HTTP request completed"
        assert kwargs["method"] == "GET"
        assert kwargs["url"] == "/api/v1/resource"
        assert kwargs["status_code"] == 200
        assert kwargs["duration_ms"] == 500.0  # 0.5 секунды в миллисекундах
        assert kwargs["user_id"] == "123"
