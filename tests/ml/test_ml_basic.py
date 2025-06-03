import numpy as np
import pytest

class TestMLEnvironment:
    """Test ML environment setup."""

    def test_numpy_installation(self):
        """Test NumPy is properly installed."""
        assert np.__version__ is not None
        # Test basic array operations
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([4.0, 5.0, 6.0])
        result = np.add(x, y)
        expected = np.array([5.0, 7.0, 9.0])
        np.testing.assert_allclose(result, expected)

    def test_numpy_operations(self):
        """Test NumPy operations."""
        np_array = np.array([1, 2, 3])
        
        assert np_array.shape == (3,)
        assert np_array.dtype == np.int64

    def test_basic_model(self):
        """Basic model operations using NumPy."""
        # Создаем простую линейную модель с NumPy
        weights = np.random.randn(10, 1)
        bias = np.random.randn(1)
        x = np.random.randn(100, 10)
        
        # Простая линейная модель: y = Wx + b
        result = np.dot(x, weights) + bias
        
        assert result.shape == (100, 1)