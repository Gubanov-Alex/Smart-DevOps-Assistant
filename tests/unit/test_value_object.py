"""Тесты для объектов-значений домена."""

from datetime import datetime

import pytest

from app.domain.value_objects import AnomalyScore, MetricValue, SourceSystem


class TestAnomalyScore:
    """Тесты для объекта-значения AnomalyScore."""

    def test_valid_anomaly_score_creation(self):
        """Тест создания валидного объекта аномалии."""
        score = AnomalyScore(value=0.8, confidence=0.9, threshold=0.7)

        assert score.value == 0.8
        assert score.confidence == 0.9
        assert score.threshold == 0.7

    def test_anomaly_score_with_default_threshold(self):
        """Тест создания с дефолтным порогом."""
        score = AnomalyScore(value=0.5, confidence=0.8)

        assert score.threshold == 0.7

    def test_invalid_value_raises_error(self):
        """Тест что неверное значение вызывает ошибку."""
        with pytest.raises(ValueError, match="Anomaly score must be between 0.0 and 1.0"):
            AnomalyScore(value=1.5, confidence=0.8)

        with pytest.raises(ValueError, match="Anomaly score must be between 0.0 and 1.0"):
            AnomalyScore(value=-0.1, confidence=0.8)

    def test_invalid_confidence_raises_error(self):
        """Тест что неверная уверенность вызывает ошибку."""
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            AnomalyScore(value=0.5, confidence=1.5)

    def test_invalid_threshold_raises_error(self):
        """Тест что неверный порог вызывает ошибку."""
        with pytest.raises(ValueError, match="Threshold must be between 0.0 and 1.0"):
            AnomalyScore(value=0.5, confidence=0.8, threshold=1.5)

    def test_is_anomaly_true(self):
        """Тест определения аномалии - положительный случай."""
        score = AnomalyScore(value=0.8, confidence=0.9, threshold=0.7)
        assert score.is_anomaly()

    def test_is_anomaly_false_low_value(self):
        """Тест определения аномалии - низкое значение."""
        score = AnomalyScore(value=0.6, confidence=0.9, threshold=0.7)
        assert not score.is_anomaly()

    def test_is_anomaly_false_low_confidence(self):
        """Тест определения аномалии - низкая уверенность."""
        score = AnomalyScore(value=0.8, confidence=0.7, threshold=0.7)
        assert not score.is_anomaly()

    def test_severity_level_normal(self):
        """Тест уровня серьезности - нормальный."""
        score = AnomalyScore(value=0.5, confidence=0.7, threshold=0.7)
        assert score.severity_level() == "normal"

    def test_severity_level_medium(self):
        """Тест уровня серьезности - средний."""
        score = AnomalyScore(value=0.75, confidence=0.9, threshold=0.7)
        assert score.severity_level() == "medium"

    def test_severity_level_high(self):
        """Тест уровня серьезности - высокий."""
        score = AnomalyScore(value=0.85, confidence=0.9, threshold=0.7)
        assert score.severity_level() == "high"

    def test_severity_level_critical(self):
        """Тест уровня серьезности - критический."""
        score = AnomalyScore(value=0.95, confidence=0.9, threshold=0.7)
        assert score.severity_level() == "critical"

    def test_anomaly_score_immutability(self):
        """Тест неизменяемости объекта."""
        score = AnomalyScore(value=0.8, confidence=0.9)

        with pytest.raises(AttributeError):
            score.value = 0.5


class TestMetricValue:
    """Тесты для объекта-значения MetricValue."""

    def test_valid_metric_creation(self):
        """Тест создания валидной метрики."""
        timestamp = datetime.now()
        metric = MetricValue(name="cpu_usage", value=75.5, unit="%", timestamp=timestamp)

        assert metric.name == "cpu_usage"
        assert metric.value == 75.5
        assert metric.unit == "%"
        assert metric.timestamp == timestamp

    def test_metric_without_timestamp(self):
        """Тест создания метрики без временной метки."""
        metric = MetricValue(name="memory_usage", value=1024, unit="MB")

        assert metric.timestamp is None

    def test_empty_name_raises_error(self):
        """Тест что пустое имя вызывает ошибку."""
        with pytest.raises(ValueError, match="Metric name cannot be empty"):
            MetricValue(name="", value=100, unit="MB")

        with pytest.raises(ValueError, match="Metric name cannot be empty"):
            MetricValue(name="   ", value=100, unit="MB")

    def test_negative_value_for_non_negative_metric(self):
        """Тест что отрицательные значения для обычных метрик вызывают ошибку."""
        with pytest.raises(ValueError, match="cannot have negative value"):
            MetricValue(name="memory_usage", value=-100, unit="MB")

    def test_negative_value_allowed_for_temperature(self):
        """Тест что отрицательные значения разрешены для температуры."""
        metric = MetricValue(name="cpu_temperature", value=-10, unit="C")
        assert metric.value == -10

    def test_negative_value_allowed_for_balance(self):
        """Тест что отрицательные значения разрешены для баланса."""
        metric = MetricValue(name="account_balance", value=-500, unit="USD")
        assert metric.value == -500

    def test_is_percentage_true(self):
        """Тест определения процентных метрик."""
        metric1 = MetricValue(name="cpu_usage", value=75, unit="%")
        metric2 = MetricValue(name="disk_usage", value=80, unit="percent")
        metric3 = MetricValue(name="memory_usage", value=90, unit="percentage")

        assert metric1.is_percentage()
        assert metric2.is_percentage()
        assert metric3.is_percentage()

    def test_is_percentage_false(self):
        """Тест для не-процентных метрик."""
        metric = MetricValue(name="memory_usage", value=1024, unit="MB")
        assert not metric.is_percentage()

    def test_normalize_percentage_over_100(self):
        """Тест нормализации процентов больше 100."""
        metric = MetricValue(name="cpu_usage", value=150, unit="%")
        assert metric.normalize_percentage() == 1.5

    def test_normalize_percentage_under_1(self):
        """Тест нормализации процентов меньше 1."""
        metric = MetricValue(name="cpu_usage", value=0.8, unit="%")
        assert metric.normalize_percentage() == 0.8

    def test_normalize_non_percentage(self):
        """Тест нормализации не-процентных значений."""
        metric = MetricValue(name="memory_usage", value=1024, unit="MB")
        assert metric.normalize_percentage() == 1024


class TestSourceSystem:
    """Тесты для объекта-значения SourceSystem."""

    def test_valid_source_system_creation(self):
        """Тест создания валидной системы-источника."""
        source = SourceSystem(name="auth-service", environment="production", service_type="api")

        assert source.name == "auth-service"
        assert source.environment == "production"
        assert source.service_type == "api"

    def test_invalid_environment_raises_error(self):
        """Тест что неверная среда вызывает ошибку."""
        with pytest.raises(ValueError, match="Environment must be one of"):
            SourceSystem(name="test-service", environment="invalid", service_type="api")

    def test_empty_name_raises_error(self):
        """Тест что пустое имя вызывает ошибку."""
        with pytest.raises(ValueError, match="Source name cannot be empty"):
            SourceSystem(name="", environment="development", service_type="api")

    def test_is_production_true(self):
        """Тест определения продакшн среды - положительный случай."""
        source = SourceSystem(name="api-service", environment="production", service_type="api")
        assert source.is_production()

    def test_is_production_false(self):
        """Тест определения продакшн среды - отрицательный случай."""
        source = SourceSystem(name="api-service", environment="staging", service_type="api")
        assert not source.is_production()

    def test_full_identifier(self):
        """Тест генерации полного идентификатора."""
        source = SourceSystem(name="auth-service", environment="production", service_type="api")

        expected = "production.api.auth-service"
        assert source.full_identifier() == expected

    def test_source_system_immutability(self):
        """Тест неизменяемости объекта."""
        source = SourceSystem(name="test", environment="development", service_type="api")

        with pytest.raises(AttributeError):
            source.name = "modified"
