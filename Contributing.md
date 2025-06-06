# Contributing to Smart DevOps Assistant

Thank you for your interest in contributing! This document provides guidelines for contributing to the Smart DevOps Assistant project.

## 🚀 Quick Start

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/Gubanov-Alex/smart-devops-assistant.git
   cd smart-devops-assistant
   ```

3. **Set up development environment**:
   ```bash
   # Install Poetry (if not installed)
   curl -sSL https://install.python-poetry.org | python3 -

   # Install dependencies
   poetry install

   # Copy environment configuration
   cp .env.example .env
   ```

4. **Start development services**:
   ```bash
   docker-compose up -d postgres redis
   ```

5. **Run the application**:
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

## 🏗️ Development Workflow

### 1. Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Changes
- Follow the existing code style and patterns
- Write tests for new functionality
- Update documentation as needed

### 3. Run Tests
```bash
# Run all tests
poetry run pytest

# Run specific test categories
poetry run pytest tests/unit/
poetry run pytest tests/integration/
poetry run pytest tests/ml/

# Check code coverage
poetry run pytest --cov=app --cov-report=html
```

### 4. Code Quality Checks
```bash
# Run pre-commit hooks
poetry run pre-commit run --all-files

# Type checking
poetry run mypy app/

# Security check
poetry run bandit -r app/
```

### 5. Commit Changes
We use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat: add log classification model"
git commit -m "fix: resolve database connection issue"  
git commit -m "docs: update API documentation"
git commit -m "test: add unit tests for anomaly detection"
```

**Commit Types:**
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `test`: Adding or modifying tests
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `ci`: CI/CD changes

### 6. Submit Pull Request
1. Push your branch to your fork
2. Create a Pull Request on GitHub
3. Fill out the PR template
4. Wait for review and address feedback

## 📝 Code Style Guidelines

### Python Code Style
- **Line length**: 100 characters
- **Type hints**: Required for all functions
- **Docstrings**: Google style for public functions

Example:
```python
from typing import List, Optional
from datetime import datetime

def analyze_logs(
    logs: List[str], 
    include_metadata: bool = True
) -> Optional[dict]:
    """Analyze log entries using ML models.
    
    Args:
        logs: List of log messages to analyze
        include_metadata: Whether to include analysis metadata
        
    Returns:
        Analysis results dictionary or None if analysis fails
        
    Raises:
        AnalysisError: If log analysis fails
    """
    # Implementation here
    pass
```

### Architecture Patterns
- **Domain-Driven Design**: Business logic in domain layer
- **Dependency Injection**: Use Protocol-based interfaces
- **SOLID Principles**: Follow all five principles
- **Error Handling**: Use custom exceptions with context

## 🧪 Testing Guidelines

### Test Structure
```
tests/
├── unit/           # Fast, isolated unit tests
├── integration/    # Integration tests with external services
├── ml/            # ML model-specific tests
└── conftest.py    # Shared test fixtures
```

### Writing Tests
- **Naming**: `test_feature_description`
- **Structure**: Arrange, Act, Assert
- **Fixtures**: Use pytest fixtures for common setup
- **Mocking**: Mock external dependencies

Example:
```python
import pytest
from unittest.mock import AsyncMock

def test_log_classification_success(mock_ml_service):
    # Arrange
    logs = ["ERROR: Database failed", "INFO: User login"]
    expected_results = [LogLevel.ERROR, LogLevel.INFO]
    mock_ml_service.classify.return_value = expected_results
    
    # Act
    results = await classify_logs(logs, mock_ml_service)
    
    # Assert
    assert len(results) == 2
    assert results[0].level == LogLevel.ERROR
    mock_ml_service.classify.assert_called_once_with(logs)
```

## 🔧 Environment Setup

### Required Tools
- **Python**: 3.12 or higher
- **Poetry**: For dependency management
- **Docker**: For local services
- **Git**: For version control

### Optional Tools
- **PyCharm/VSCode**: IDE with Python support
- **Postman**: For API testing
- **k6/Artillery**: For load testing

### Development Services
The `docker-compose.yml` provides:
- **PostgreSQL**: Database
- **Redis**: Caching and message queue
- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization

## 📚 Documentation

### API Documentation
- Use FastAPI's automatic OpenAPI generation
- Add detailed docstrings to endpoints
- Include request/response examples

### Code Documentation
- Document complex algorithms and business logic
- Use type hints extensively
- Add ADRs (Architecture Decision Records) for major decisions

## 🐛 Bug Reports

When reporting bugs, include:
- **Environment details** (OS, Python version, Docker version)
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Error logs** and stack traces
- **Screenshots** if applicable

## 💡 Feature Requests

For new features:
- **Describe the problem** the feature would solve
- **Propose a solution** with implementation details
- **Consider alternatives** and their trade-offs
- **Estimate impact** on performance and complexity

## 🏆 Recognition

Contributors will be:
- **Listed in README** with their contributions
- **Mentioned in release notes** for significant contributions
- **Given credit** in blog posts and presentations

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and ideas
- **Email**: your.email@example.com for private matters

## 📄 License

By contributing, you agree that your contributions will be licensed under the same [MIT License](LICENSE) that covers the project.
