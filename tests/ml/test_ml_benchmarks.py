"""ML model performance benchmark tests."""
import pytest
import torch
import numpy as np
from typing import Dict, Any, List


class TestMLBenchmarks:
    """Performance benchmark tests for ML models."""

    @pytest.mark.benchmark
    def test_linear_model_benchmark(self, benchmark: Any) -> None:
        """Benchmark linear model performance."""
        def create_and_run_model() -> torch.Tensor:
            model = torch.nn.Linear(100, 50)
            x = torch.randn(1000, 100)
            return model(x)

        result = benchmark(create_and_run_model)
        assert result.shape == (1000, 50)

    @pytest.mark.benchmark
    def test_tensor_operations_benchmark(self, benchmark: Any) -> None:
        """Benchmark basic tensor operations."""
        def tensor_operations() -> torch.Tensor:
            x = torch.randn(1000, 1000)
            y = torch.randn(1000, 1000)
            return torch.matmul(x, y)

        result = benchmark(tensor_operations)
        assert result.shape == (1000, 1000)

    @pytest.mark.benchmark
    def test_numpy_pytorch_conversion_benchmark(self, benchmark: Any) -> None:
        """Benchmark NumPy to PyTorch conversion."""
        def convert_data() -> torch.Tensor:
            np_data = np.random.randn(1000, 100)
            torch_data = torch.from_numpy(np_data)
            return torch_data.float()

        result = benchmark(convert_data)
        assert result.shape == (1000, 100)
        assert result.dtype == torch.float32


class TestLogProcessingBenchmarks:
    """Benchmark tests for log processing."""

    @pytest.mark.benchmark
    def test_log_parsing_benchmark(self, benchmark: Any, sample_log_data: Dict[str, Any]) -> None:
        """Benchmark log parsing performance."""
        def parse_logs() -> List[Dict[str, Any]]:
            # Simulate log parsing
            logs = [sample_log_data.copy() for _ in range(1000)]
            parsed = []
            for log in logs:
                features = {
                    "length": len(log["message"]),
                    "level": log["level"],
                    "has_trace": bool(log.get("trace_id"))
                }
                parsed.append(features)
            return parsed

        result = benchmark(parse_logs)
        assert len(result) == 1000
        assert all("length" in item for item in result)