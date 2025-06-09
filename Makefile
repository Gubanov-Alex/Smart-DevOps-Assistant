# Smart DevOps Assistant - Professional Makefile
# ===============================================
# Requires: Poetry, Docker, Docker Compose

# Configuration
PROJECT_NAME := smart-devops-assistant
PYTHON_VERSION := 3.12
POETRY_VERSION := 1.8.3
DOCKER_REGISTRY := ghcr.io
IMAGE_NAME := $(DOCKER_REGISTRY)/$(shell whoami)/$(PROJECT_NAME)

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Environment detection
ENV ?= development
ifeq ($(ENV),production)
	DOCKER_FILE := docker/Dockerfile.prod
	COMPOSE_FILE := docker-compose.prod.yml
else
	DOCKER_FILE := docker/Dockerfile.dev
	COMPOSE_FILE := docker-compose.yml
endif

.PHONY: help install dev test lint format security build deploy clean

# Default target
.DEFAULT_GOAL := help

## Development Environment
install: ## Install all dependencies and setup development environment
	@echo "$(BLUE)Installing Poetry $(POETRY_VERSION)...$(NC)"
	@curl -sSL https://install.python-poetry.org | python3 - --version $(POETRY_VERSION)
	@echo "$(BLUE)Installing project dependencies...$(NC)"
	@poetry install --no-interaction
	@echo "$(BLUE)Setting up pre-commit hooks...$(NC)"
	@poetry run pre-commit install
	@echo "$(GREEN)✅ Development environment ready!$(NC)"

dev: ## Start development server with hot reload
	@echo "$(BLUE)Starting development server...$(NC)"
	@poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-services: ## Start development services (PostgreSQL, Redis)
	@echo "$(BLUE)Starting development services...$(NC)"
	@docker-compose up -d postgres redis
	@echo "$(GREEN)✅ Services started: postgres, redis$(NC)"

dev-full: ## Start full development environment
	@echo "$(BLUE)Starting full development environment...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)✅ Full development environment running$(NC)"

## Code Quality & Testing
lint: ## Run all linting tools (flake8, bandit)
	@echo "$(BLUE)Running code quality checks...$(NC)"
	@poetry run flake8 app/ tests/
	@poetry run bandit -r app/ -ll
	@echo "$(GREEN)✅ Linting completed$(NC)"

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	@poetry run black app/ tests/
	@poetry run isort app/ tests/
	@echo "$(GREEN)✅ Code formatted$(NC)"

format-check: ## Check code formatting without making changes
	@echo "$(BLUE)Checking code formatting...$(NC)"
	@poetry run black --check app/ tests/
	@poetry run isort --check-only app/ tests/

security: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	@poetry run bandit -r app/ -f json -o bandit-report.json
	@if command -v poetry run safety &> /dev/null; then \
		poetry run safety check --json > safety-report.json || echo "$(YELLOW)⚠️ Safety check completed with warnings$(NC)"; \
	else \
		echo "$(YELLOW)⚠️ Safety not installed, skipping vulnerability check$(NC)"; \
	fi
	@echo "$(GREEN)✅ Security scan completed$(NC)"

test: ## Run all tests with coverage
	@echo "$(BLUE)Running test suite...$(NC)"
	@poetry run pytest tests/ \
		--cov=app \
		--cov-report=html:htmlcov \
		--cov-report=xml:coverage.xml \
		--cov-report=term-missing \
		--cov-fail-under=75 \
		-v
	@echo "$(GREEN)✅ Tests completed$(NC)"

benchmark: ## Run performance benchmarks
	@echo "$(BLUE)Running benchmarks...$(NC)"
	@poetry run pytest tests/ -m benchmark \
		--benchmark-only \
		--benchmark-json=benchmark-results.json \
		--benchmark-sort=mean \
		--benchmark-group-by=func \
		--benchmark-warmup=on \
		--benchmark-disable-gc
	@echo "$(GREEN)✅ Benchmarks completed$(NC)"

test-unit: ## Run only unit tests (fast)
	@echo "$(BLUE)Running unit tests...$(NC)"
	@poetry run pytest tests/unit/ -v --tb=short \
		--cov=app \
		--cov-report=term-missing

test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	@docker-compose up -d postgres redis
	@poetry run pytest tests/integration/ -v
	@docker-compose down

test-ml: ## Run ML model tests
	@echo "$(BLUE)Running ML tests...$(NC)"
	@poetry run pytest tests/ml/ -v --tb=short

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	@poetry run ptw tests/ app/ -- --tb=short -v

test-all: ## Run all tests excluding benchmarks
	@echo "$(BLUE)Running all tests (excluding benchmarks)...$(NC)"
	@poetry run pytest tests/ \
		-m "not benchmark" \
		--cov=app \
		--cov-report=html:htmlcov \
		--cov-report=xml:coverage.xml \
		--cov-report=term-missing \
		--cov-fail-under=60 \
		-v
	@echo "$(GREEN)✅ All tests completed$(NC)"

## Quality Assurance
qa: format lint security test ## Run complete quality assurance pipeline
	@echo "$(GREEN)✅ QA pipeline completed successfully!$(NC)"

pre-commit: ## Run pre-commit hooks on all files
	@echo "$(BLUE)Running pre-commit hooks...$(NC)"
	@poetry run pre-commit run --all-files

ci-check: ## Simulate CI pipeline locally
	@echo "$(BLUE)Simulating CI pipeline...$(NC)"
	@$(MAKE) format-check
	@$(MAKE) lint
	@$(MAKE) security
	@$(MAKE) test-all  # Используем test-all вместо test
	@echo "$(GREEN)✅ CI simulation passed!$(NC)"

## Docker & Deployment
build: ## Build Docker image for current environment
	@echo "$(BLUE)Building Docker image for $(ENV)...$(NC)"
	@docker build -f $(DOCKER_FILE) -t $(IMAGE_NAME):$(ENV) .
	@docker tag $(IMAGE_NAME):$(ENV) $(IMAGE_NAME):latest
	@echo "$(GREEN)✅ Image built: $(IMAGE_NAME):$(ENV)$(NC)"

build-prod: ## Build production Docker image
	@echo "$(BLUE)Building production Docker image...$(NC)"
	@ENV=production $(MAKE) build
	@docker tag $(IMAGE_NAME):production $(IMAGE_NAME):$(shell git rev-parse --short HEAD)
	@echo "$(GREEN)✅ Production image built$(NC)"

push: ## Push Docker image to registry
	@echo "$(BLUE)Pushing image to registry...$(NC)"
	@docker push $(IMAGE_NAME):$(ENV)
	@docker push $(IMAGE_NAME):latest
	@echo "$(GREEN)✅ Image pushed$(NC)"

deploy-dev: ## Deploy to development environment
	@echo "$(BLUE)Deploying to development...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) up -d
	@echo "$(GREEN)✅ Deployed to development$(NC)"

deploy-prod: build-prod push ## Build and deploy to production
	@echo "$(BLUE)Deploying to production...$(NC)"
	@ENV=production docker-compose -f docker-compose.prod.yml up -d
	@echo "$(GREEN)✅ Deployed to production$(NC)"

## Database Operations
db-upgrade: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	@poetry run alembic upgrade head
	@echo "$(GREEN)✅ Database upgraded$(NC)"

db-migrate: ## Create new migration
	@echo "$(BLUE)Creating new migration...$(NC)"
	@poetry run alembic revision --autogenerate -m "$(MSG)"
	@echo "$(GREEN)✅ Migration created$(NC)"

db-reset: ## Reset database (DANGEROUS!)
	@echo "$(RED)⚠️  This will delete all data! Press Ctrl+C to cancel...$(NC)"
	@sleep 5
	@docker-compose down -v
	@docker-compose up -d postgres
	@sleep 5
	@poetry run alembic upgrade head
	@echo "$(GREEN)✅ Database reset$(NC)"

## ML Operations
ml-train: ## Train ML models
	@echo "$(BLUE)Training ML models...$(NC)"
	@poetry run python -m app.ml.train --model log_classifier
	@echo "$(GREEN)✅ ML training completed$(NC)"

ml-evaluate: ## Evaluate ML models
	@echo "$(BLUE)Evaluating ML models...$(NC)"
	@poetry run python -m app.ml.evaluate --model log_classifier
	@echo "$(GREEN)✅ ML evaluation completed$(NC)"

ml-export: ## Export models for production
	@echo "$(BLUE)Exporting models...$(NC)"
	@poetry run python -m app.ml.export --model log_classifier --format onnx
	@echo "$(GREEN)✅ Models exported$(NC)"

## Documentation
docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	@poetry run mkdocs build
	@echo "$(GREEN)✅ Documentation generated$(NC)"

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation at http://localhost:8001$(NC)"
	@poetry run mkdocs serve -a localhost:8001

docs-deploy: ## Deploy documentation to GitHub Pages
	@echo "$(BLUE)Deploying documentation...$(NC)"
	@poetry run mkdocs gh-deploy
	@echo "$(GREEN)✅ Documentation deployed$(NC)"

## Utilities
logs: ## Show application logs
	@echo "$(BLUE)Showing application logs...$(NC)"
	@docker-compose logs -f app

logs-db: ## Show database logs
	@echo "$(BLUE)Showing database logs...$(NC)"
	@docker-compose logs -f postgres

shell: ## Open interactive shell in container
	@echo "$(BLUE)Opening shell in container...$(NC)"
	@docker-compose exec app poetry run python

psql: ## Connect to PostgreSQL database
	@echo "$(BLUE)Connecting to PostgreSQL...$(NC)"
	@docker-compose exec postgres psql -U devops -d devops_assistant

redis-cli: ## Connect to Redis
	@echo "$(BLUE)Connecting to Redis...$(NC)"
	@docker-compose exec redis redis-cli

## Monitoring & Health
health: ## Check application health
	@echo "$(BLUE)Checking application health...$(NC)"
	@curl -f http://localhost:8000/health || echo "$(RED)❌ Health check failed$(NC)"

metrics: ## Show application metrics
	@echo "$(BLUE)Fetching metrics...$(NC)"
	@curl -s http://localhost:8000/metrics || echo "$(RED)❌ Metrics unavailable$(NC)"

monitor: ## Open monitoring dashboard
	@echo "$(BLUE)Opening monitoring dashboard...$(NC)"
	@open http://localhost:3000 || echo "Visit http://localhost:3000"

## Cleanup
clean: ## Clean up temporary files and containers
	@echo "$(BLUE)Cleaning up...$(NC)"
	@docker-compose down -v
	@docker system prune -f
	@rm -rf .pytest_cache/
	@rm -rf htmlcov/
	@rm -rf .coverage
	@rm -rf dist/
	@rm -rf build/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup completed$(NC)"

clean-images: ## Remove all project Docker images
	@echo "$(BLUE)Removing Docker images...$(NC)"
	@docker images $(IMAGE_NAME) -q | xargs -r docker rmi -f
	@echo "$(GREEN)✅ Images removed$(NC)"

## Information
status: ## Show project status
	@echo "$(BLUE)Project Status:$(NC)"
	@echo "Environment: $(ENV)"
	@echo "Docker Image: $(IMAGE_NAME):$(ENV)"
	@echo "Python Version: $(PYTHON_VERSION)"
	@echo "Poetry Version: $(POETRY_VERSION)"
	@echo ""
	@echo "$(BLUE)Services Status:$(NC)"
	@docker-compose ps 2>/dev/null || echo "No services running"

deps: ## Show dependency tree
	@echo "$(BLUE)Dependency tree:$(NC)"
	@poetry show --tree

outdated: ## Check for outdated dependencies
	@echo "$(BLUE)Checking for outdated dependencies...$(NC)"
	@poetry show --outdated

update: ## Update dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	@poetry update
	@echo "$(GREEN)✅ Dependencies updated$(NC)"

## Release Management
version: ## Show current version
	@poetry version

bump-patch: ## Bump patch version
	@poetry version patch
	@echo "$(GREEN)✅ Version bumped to $(shell poetry version -s)$(NC)"

bump-minor: ## Bump minor version
	@poetry version minor
	@echo "$(GREEN)✅ Version bumped to $(shell poetry version -s)$(NC)"

bump-major: ## Bump major version
	@poetry version major
	@echo "$(GREEN)✅ Version bumped to $(shell poetry version -s)$(NC)"

release: ## Create release (bump version, tag, push)
	@echo "$(BLUE)Creating release...$(NC)"
	@poetry version patch
	@git add pyproject.toml
	@git commit -m "Bump version to $(shell poetry version -s)"
	@git tag v$(shell poetry version -s)
	@git push origin main --tags
	@echo "$(GREEN)✅ Release v$(shell poetry version -s) created$(NC)"

.PHONY: build-fast build-full dev up clean logs test

# Environment setup
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Быстрая сборка (только базовые сервисы)
build-fast:
	docker-compose build api

# Полная сборка с проверкой изменений
build-full:
	@if [ pyproject.toml -nt .build-cache ] || [ poetry.lock -nt .build-cache ]; then \
		echo "Dependencies changed, full rebuild..."; \
		docker-compose build --no-cache; \
		touch .build-cache; \
	else \
		echo "No dependency changes, using cache..."; \
		docker-compose build; \
	fi
	@echo "  make test                   - Run tests with coverage"
	@echo "  make ENV=production build   - Build production image"
	@echo "  make deploy-prod            - Deploy to production"
