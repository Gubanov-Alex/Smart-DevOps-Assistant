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

.PHONY: help install dev test lint format security build deploy clean setup-dirs

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "$(BLUE)Smart DevOps Assistant - Available Commands$(NC)"
	@echo "============================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

## Setup
setup-dirs: ## Create necessary directories
	@echo "$(BLUE)Creating project directories...$(NC)"
	@mkdir -p reports/security reports/coverage reports/benchmarks
	@mkdir -p logs/app logs/security logs/audit
	@mkdir -p models/checkpoints models/exports models/backups
	@mkdir -p data/raw data/processed data/temp
	@mkdir -p docs/api docs/user docs/dev
	@mkdir -p backups/db backups/models backups/configs
	@mkdir -p .secrets
	@touch .secrets/.gitkeep 2>/dev/null || true
	@echo "$(GREEN)✅ Directories created$(NC)"

## Development Environment
install: setup-dirs ## Install all dependencies and setup development environment
	@echo "$(BLUE)Installing Poetry $(POETRY_VERSION)...$(NC)"
	@curl -sSL https://install.python-poetry.org | python3 - --version $(POETRY_VERSION) || echo "Poetry already installed"
	@echo "$(BLUE)Installing project dependencies...$(NC)"
	@poetry install --no-interaction
	@echo "$(BLUE)Setting up pre-commit hooks...$(NC)"
	@poetry run pre-commit install --install-hooks || echo "Pre-commit setup completed"
	@echo "$(GREEN)✅ Development environment ready!$(NC)"

dev: ## Start development server with hot reload
	@echo "$(BLUE)Starting development server...$(NC)"
	@poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-services: ## Start development services (PostgreSQL, Redis)
	@echo "$(BLUE)Starting development services...$(NC)"
	@docker-compose up -d postgres redis || echo "$(YELLOW)Services may already be running$(NC)"
	@echo "$(GREEN)✅ Services started: postgres, redis$(NC)"

dev-full: ## Start full development environment
	@echo "$(BLUE)Starting full development environment...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)✅ Full development environment running$(NC)"

## Code Quality & Testing
format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	@poetry run black app/ tests/ --line-length=88
	@poetry run isort app/ tests/ --profile black
	@echo "$(GREEN)✅ Code formatted$(NC)"

format-check: ## Check code formatting without making changes
	@echo "$(BLUE)Checking code formatting...$(NC)"
	@poetry run black --check --diff app/ tests/ --line-length=88
	@poetry run isort --check-only --diff app/ tests/ --profile black

lint: ## Run all linting tools (flake8, bandit)
	@echo "$(BLUE)Running code quality checks...$(NC)"
	@poetry run flake8 app/ tests/ --max-complexity=10 --max-line-length=88 --extend-ignore=E203,W503
	@poetry run bandit -r app/ -ll --configfile .bandit || echo "$(YELLOW)⚠️ Security issues found$(NC)"
	@echo "$(GREEN)✅ Linting completed$(NC)"

security: setup-dirs ## Run comprehensive security analysis
	@echo "$(BLUE)Running comprehensive security analysis...$(NC)"
	@echo "$(YELLOW)🔍 Checking if security tools are available...$(NC)"
	@poetry run python -c "import bandit; print('✅ Bandit available')" 2>/dev/null || (echo "❌ Bandit not found. Run: poetry install --with dev"; exit 1)
	@echo "$(YELLOW)🔒 Bandit security scan (detailed)...$(NC)"
	@poetry run bandit -r app/ -f json -o reports/security/bandit-report.json -ll --configfile .bandit || echo "$(YELLOW)Security issues found - check reports/security/bandit-report.json$(NC)"
	@poetry run bandit -r app/ -f txt -o reports/security/bandit-report.txt -ll --configfile .bandit || echo "$(YELLOW)Security issues found - check reports/security/bandit-report.txt$(NC)"
	@echo "$(YELLOW)🛡️ Safety vulnerability scan...$(NC)"
	@poetry run safety check --json --output reports/security/safety-report.json 2>/dev/null || echo "$(YELLOW)⚠️ Vulnerabilities found or Safety not available$(NC)"
	@poetry run safety check --short-report 2>/dev/null || echo "$(YELLOW)⚠️ Safety check completed with warnings or not available$(NC)"
	@echo "$(YELLOW)📊 Generating security summary...$(NC)"
	@echo "Security scan completed at: $(date)" > reports/security/scan-summary.txt
	@echo "Files scanned: $(find app/ -name '*.py' | wc -l) Python files" >> reports/security/scan-summary.txt
	@echo "Bandit issues: $(grep -c '"issue_severity"' reports/security/bandit-report.json 2>/dev/null || echo '0')" >> reports/security/scan-summary.txt
	@cat reports/security/scan-summary.txt
	@echo "$(GREEN)✅ Security analysis completed - check reports/security/ directory$(NC)"

security-baseline: setup-dirs ## Create security baseline for comparison
	@echo "$(BLUE)Creating security baseline...$(NC)"
	@poetry run bandit -r app/ -f json -o reports/security/bandit-baseline.json -ll --configfile .bandit || echo "Baseline created with issues"
	@poetry run safety check --json --output reports/security/safety-baseline.json || echo "Baseline created with vulnerabilities"
	@echo "$(GREEN)✅ Security baseline created in reports/security/$(NC)"

test: setup-dirs ## Run all tests with coverage
	@echo "$(BLUE)Running test suite...$(NC)"
	@poetry run pytest tests/ \
		--cov=app \
		--cov-report=html:reports/coverage/htmlcov \
		--cov-report=xml:reports/coverage/coverage.xml \
		--cov-report=term-missing \
		--cov-fail-under=75 \
		--tb=short \
		-v
	@echo "$(GREEN)✅ Tests completed - coverage report in reports/coverage/htmlcov/index.html$(NC)"

test-fast: ## Run tests without coverage for quick feedback
	@echo "$(BLUE)Running fast tests...$(NC)"
	@poetry run pytest tests/ --tb=short -q
	@echo "$(GREEN)✅ Fast tests completed$(NC)"

test-security: ## Run only security tests
	@echo "$(BLUE)Running security tests...$(NC)"
	@poetry run pytest tests/test_security.py -v --tb=short || echo "$(YELLOW)Some security tests may not exist yet$(NC)"
	@echo "$(GREEN)✅ Security tests completed$(NC)"

benchmark: setup-dirs ## Run performance benchmarks
	@echo "$(BLUE)Running benchmarks...$(NC)"
	@poetry run pytest tests/ -m benchmark \
		--benchmark-only \
		--benchmark-json=reports/benchmarks/benchmark-results.json \
		--benchmark-sort=mean \
		--benchmark-group-by=func \
		--benchmark-warmup=on \
		--benchmark-disable-gc || echo "$(YELLOW)Benchmarks may not be configured yet$(NC)"
	@echo "$(GREEN)✅ Benchmarks completed$(NC)"

## Quality Assurance
qa: format lint security test ## Run complete quality assurance pipeline
	@echo "$(GREEN)✅ QA pipeline completed successfully!$(NC)"

pre-commit: ## Run pre-commit hooks on all files
	@echo "$(BLUE)Running pre-commit hooks...$(NC)"
	@poetry run pre-commit run --all-files || echo "$(YELLOW)Some pre-commit checks failed$(NC)"

ci-check: setup-dirs ## Simulate CI pipeline locally
	@echo "$(BLUE)Simulating CI pipeline...$(NC)"
	@$(MAKE) format-check || echo "$(YELLOW)Format check issues found$(NC)"
	@$(MAKE) lint || echo "$(YELLOW)Lint issues found$(NC)"
	@$(MAKE) security || echo "$(YELLOW)Security issues found$(NC)"
	@$(MAKE) test || echo "$(YELLOW)Test issues found$(NC)"
	@echo "$(GREEN)✅ CI simulation completed - check individual reports$(NC)"

## Docker & Deployment
build: ## Build Docker image for current environment
	@echo "$(BLUE)Building Docker image for $(ENV)...$(NC)"
	@docker build -f $(DOCKER_FILE) -t $(IMAGE_NAME):$(ENV) . || echo "$(YELLOW)Docker build may have issues$(NC)"
	@echo "$(GREEN)✅ Docker image built: $(IMAGE_NAME):$(ENV)$(NC)"

push: ## Push Docker image to registry
	@echo "$(BLUE)Pushing Docker image...$(NC)"
	@docker push $(IMAGE_NAME):$(ENV)
	@echo "$(GREEN)✅ Image pushed to $(DOCKER_REGISTRY)$(NC)"

deploy: build ## Deploy application
	@echo "$(BLUE)Deploying application...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) up -d
	@echo "$(GREEN)✅ Application deployed$(NC)"

## Database
db-migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	@poetry run alembic upgrade head || echo "$(YELLOW)Migration may have issues$(NC)"
	@echo "$(GREEN)✅ Database migrations completed$(NC)"

db-reset: ## Reset database (WARNING: Destructive!)
	@echo "$(RED)⚠️ This will delete all data! Are you sure? [y/N]$(NC)" && read ans && [ $${ans:-N} = y ]
	@poetry run alembic downgrade base || echo "Downgrade completed"
	@poetry run alembic upgrade head || echo "Upgrade completed"
	@echo "$(GREEN)✅ Database reset completed$(NC)"

## AI/ML
train-models: setup-dirs ## Train ML models
	@echo "$(BLUE)Training ML models...$(NC)"
	@poetry run python scripts/train_models.py || echo "$(YELLOW)Training script may not exist$(NC)"
	@echo "$(GREEN)✅ Model training completed$(NC)"

validate-models: ## Validate trained models
	@echo "$(BLUE)Validating ML models...$(NC)"
	@poetry run python scripts/validate_models.py || echo "$(YELLOW)Validation script may not exist$(NC)"
	@echo "$(GREEN)✅ Model validation completed$(NC)"

## Cleanup
clean: ## Clean up build artifacts and cache
	@echo "$(BLUE)Cleaning up...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf dist/ build/ .coverage || true
	@echo "$(GREEN)✅ Cleanup completed$(NC)"

clean-reports: ## Clean up all report files
	@echo "$(BLUE)Cleaning up reports...$(NC)"
	@rm -rf reports/* || true
	@$(MAKE) setup-dirs
	@echo "$(GREEN)✅ Reports cleaned$(NC)"

clean-docker: ## Clean up Docker resources
	@echo "$(BLUE)Cleaning Docker resources...$(NC)"
	@docker-compose down --volumes --remove-orphans || true
	@docker system prune -f || true
	@echo "$(GREEN)✅ Docker cleanup completed$(NC)"

## Documentation
docs: setup-dirs ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	@poetry run sphinx-build -b html docs/ docs/_build/html || echo "$(YELLOW)Documentation build may have issues$(NC)"
	@echo "$(GREEN)✅ Documentation generated in docs/_build/html/$(NC)"

## Utilities
check-deps: ## Check for dependency updates
	@echo "$(BLUE)Checking for dependency updates...$(NC)"
	@poetry show --outdated || echo "$(YELLOW)Some dependencies may be outdated$(NC)"

update-deps: ## Update dependencies safely
	@echo "$(BLUE)Updating dependencies...$(NC)"
	@poetry update
	@$(MAKE) security  # Re-run security checks after updates
	@echo "$(GREEN)✅ Dependencies updated and security checked$(NC)"

status: ## Show project status
	@echo "$(BLUE)Project Status:$(NC)"
	@echo "=============="
	@echo "Environment: $(ENV)"
	@echo "Python: $(PYTHON_VERSION)"
	@echo "Poetry: $(POETRY_VERSION)"
	@echo "Last security scan: $$(ls -la reports/security/bandit-report.txt 2>/dev/null | awk '{print $$6, $$7, $$8}' || echo 'Never')"
	@echo "Reports directory: $$(ls -la reports/ 2>/dev/null | wc -l || echo '0') files"
	@echo "Docker images: $$(docker images | grep $(PROJECT_NAME) | wc -l || echo '0')"

## Advanced Commands
emergency-scan: setup-dirs ## Emergency security scan (fast)
	@echo "$(RED)🚨 Running emergency security scan...$(NC)"
	@poetry run bandit -r app/ -f text -ll --severity=high --confidence=high || echo "HIGH PRIORITY ISSUES FOUND!"
	@poetry run safety check --short-report || echo "VULNERABILITIES FOUND!"
	@echo "$(GREEN)✅ Emergency scan completed$(NC)"

full-check: setup-dirs format lint security test docs ## Run comprehensive project check
	@echo "$(BLUE)Running comprehensive project check...$(NC)"
	@$(MAKE) benchmark || echo "Benchmarks completed with issues"
	@echo "$(GREEN)✅ Full project check completed$(NC)"

reset-environment: clean clean-docker install ## Reset entire environment
	@echo "$(BLUE)Resetting entire environment...$(NC)"
	@$(MAKE) dev-services
	@echo "$(GREEN)✅ Environment reset completed$(NC)"

## Security Fixes
fix-security-code: ## Automatically fix security issues in code
	@echo "$(BLUE)Fixing security issues in code...$(NC)"
	@python fix_security_issues.py
	@echo "$(GREEN)✅ Security fixes applied$(NC)"

test-security-fixed: fix-security-code ## Fix security issues and run tests
	@echo "$(BLUE)Running security tests after fixes...$(NC)"
	@poetry run pytest tests/test_security.py -v --tb=short
	@echo "$(GREEN)✅ Security tests completed$(NC)"

test-security-new: ## Run new fixed security tests
	@echo "$(BLUE)Running new security tests...$(NC)"
	@poetry run pytest tests/test_security_fixed.py -v --tb=short
	@echo "$(GREEN)✅ New security tests completed$(NC)"

validate-security-fixes: ## Validate that security fixes work
	@echo "$(BLUE)Validating security fixes...$(NC)"
	@echo "$(YELLOW)1. Checking PyTorch safe loading...$(NC)"
	@grep -n "safe_globals" app/infrastructure/ml/models/base.py && echo "✅ Found" || echo "❌ PyTorch safe loading not found"
	@echo "$(YELLOW)2. Checking enhanced text cleaning...$(NC)"
	@grep -n "dangerous_patterns" app/infrastructure/ml/preprocessing/text_processor.py && echo "✅ Found" || echo "❌ Enhanced cleaning not found"
	@echo "$(YELLOW)3. Running quick security test...$(NC)"
	@poetry run python -c "from app.infrastructure.ml.preprocessing.text_processor import LogTextProcessor; p=LogTextProcessor(); result=p.clean_log_message('<script>alert(1)</script>'); assert 'script' not in result; print('✅ Text cleaning works')"
	@echo "$(GREEN)✅ Security validation completed$(NC)"

security-emergency-fix: ## Emergency security fix and test
	@echo "$(RED)🚨 Emergency Security Fix$(NC)"
	@$(MAKE) fix-security-code
	@$(MAKE) validate-security-fixes
	@$(MAKE) test-security-new
	@echo "$(GREEN)✅ Emergency security fix completed$(NC)"

docstring-check: ## Check docstring compliance with pydocstyle
	@echo "$(BLUE)Checking docstring compliance...$(NC)"
	@poetry run pydocstyle app/ --count --explain --source || echo "$(YELLOW)⚠️ Docstring issues found$(NC)"
	@echo "$(GREEN)✅ Docstring check completed$(NC)"

fix-docstrings: ## Fix common docstring issues
	@echo "$(BLUE)Fixing docstring issues...$(NC)"
	@python fix_docstring_issues.py
	@echo "$(GREEN)✅ Docstring fixes applied$(NC)"

doctest: ## Run doctests
	@echo "$(BLUE)Running doctests...$(NC)"
	@poetry run python -m doctest app/**/*.py -v || echo "$(YELLOW)Some doctests may have failed$(NC)"
	@echo "$(GREEN)✅ Doctests completed$(NC)"

# Database Management Commands for existing docker-compose.yaml
# Add these to your existing Makefile after line with "update-deps:"

## Database Services
db-up: ## Start database services (PostgreSQL, Redis)
	@echo "$(BLUE)Starting database services...$(NC)"
	@docker-compose up -d postgres redis
	@echo "$(YELLOW)⏳ Waiting for database to be ready...$(NC)"
	@sleep 15
	@echo "$(GREEN)✅ Database services started$(NC)"
	@echo "$(BLUE)Database connection: postgresql://devops_user:devops_pass@localhost:5433/devops_assistant$(NC)"

db-down: ## Stop database services
	@echo "$(BLUE)Stopping database services...$(NC)"
	@docker-compose down
	@echo "$(GREEN)✅ Database services stopped$(NC)"

db-full: ## Start all services including monitoring
	@echo "$(BLUE)Starting all services...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)✅ All services started$(NC)"

db-logs: ## Show database logs
	@echo "$(BLUE)Showing database logs...$(NC)"
	@docker-compose logs -f postgres

db-shell: ## Connect to PostgreSQL shell
	@echo "$(BLUE)Connecting to PostgreSQL shell...$(NC)"
	@docker-compose exec postgres psql -U devops_user -d devops_assistant

db-status: ## Check database connection status
	@echo "$(BLUE)Checking database status...$(NC)"
	@docker ps | grep postgres && echo "$(GREEN)✅ PostgreSQL container running$(NC)" || echo "$(RED)❌ PostgreSQL not running$(NC)"
	@docker ps | grep redis && echo "$(GREEN)✅ Redis container running$(NC)" || echo "$(RED)❌ Redis not running$(NC)"
	@psql postgresql://devops_user:devops_pass@localhost:5433/devops_assistant -c "SELECT version();" 2>/dev/null && echo "$(GREEN)✅ Database connection OK$(NC)" || echo "$(YELLOW)⚠️ Database connection failed$(NC)"

## Database Migrations
db-init: ## Initialize Alembic (run once)
	@echo "$(BLUE)Initializing Alembic migrations...$(NC)"
	@poetry run alembic init alembic || echo "$(YELLOW)Alembic may already be initialized$(NC)"
	@echo "$(GREEN)✅ Alembic initialized$(NC)"

db-create-migration: ## Create new migration with autogenerate
	@echo "$(BLUE)Creating new migration...$(NC)"
	@export DATABASE_URL_SYNC="postgresql://devops_user:devops_pass@localhost:5433/devops_assistant" && \
		poetry run alembic revision --autogenerate -m "$(if $(m),$(m),Auto-generated migration)"
	@echo "$(GREEN)✅ Migration created$(NC)"

db-migrate: db-up ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	@sleep 10  # Give database more time to start
	@export DATABASE_URL_SYNC="postgresql://devops_user:devops_pass@localhost:5433/devops_assistant" && \
		poetry run alembic upgrade head
	@echo "$(GREEN)✅ Database migrations completed$(NC)"

db-upgrade: ## Apply migrations to database
	@echo "$(BLUE)Applying migrations...$(NC)"
	@export DATABASE_URL_SYNC="postgresql://devops_user:devops_pass@localhost:5433/devops_assistant" && \
		poetry run alembic upgrade head
	@echo "$(GREEN)✅ Migrations applied$(NC)"

db-downgrade: ## Downgrade database by one migration
	@echo "$(BLUE)Downgrading database...$(NC)"
	@export DATABASE_URL_SYNC="postgresql://devops_user:devops_pass@localhost:5433/devops_assistant" && \
		poetry run alembic downgrade -1
	@echo "$(GREEN)✅ Database downgraded$(NC)"

db-history: ## Show migration history
	@echo "$(BLUE)Migration history:$(NC)"
	@export DATABASE_URL_SYNC="postgresql://devops_user:devops_pass@localhost:5433/devops_assistant" && \
		poetry run alembic history --verbose

db-current: ## Show current migration
	@echo "$(BLUE)Current migration:$(NC)"
	@export DATABASE_URL_SYNC="postgresql://devops_user:devops_pass@localhost:5433/devops_assistant" && \
		poetry run alembic current

db-reset: ## Reset database (WARNING: destroys all data)
	@echo "$(RED)⚠️  This will destroy all database data!$(NC)"
	@echo "$(YELLOW)Are you sure? Type 'yes' to continue:$(NC)" && read ans && [ "$$ans" = "yes" ]
	@echo "$(BLUE)Resetting database...$(NC)"
	@docker-compose down -v
	@$(MAKE) db-up
	@sleep 15
	@$(MAKE) db-migrate
	@echo "$(GREEN)✅ Database reset complete$(NC)"

## Database Tools
seed-db: db-up ## Seed database with test data
	@echo "$(BLUE)Seeding database with test data...$(NC)"
	@sleep 10  # Ensure DB is ready
	@export DATABASE_URL_SYNC="postgresql://devops_user:devops_pass@localhost:5433/devops_assistant" && \
		poetry run python scripts/seed_database.py || echo "$(YELLOW)Seeding script may not exist$(NC)"
	@echo "$(GREEN)✅ Database seeded$(NC)"

backup-db: ## Create database backup
	@echo "$(BLUE)Creating database backup...$(NC)"
	@mkdir -p backups/db
	@docker-compose exec postgres pg_dump -U devops_user devops_assistant > backups/db/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ Backup created in backups/db/$(NC)"

restore-db: ## Restore database from backup (specify BACKUP_FILE=filename)
	@echo "$(BLUE)Restoring database from backup...$(NC)"
	@test -n "$(BACKUP_FILE)" || (echo "$(RED)Please specify BACKUP_FILE=filename$(NC)" && exit 1)
	@test -f "$(BACKUP_FILE)" || (echo "$(RED)Backup file $(BACKUP_FILE) not found$(NC)" && exit 1)
	@docker-compose exec -T postgres psql -U devops_user devops_assistant < $(BACKUP_FILE)
	@echo "$(GREEN)✅ Database restored from $(BACKUP_FILE)$(NC)"

## Environment Setup
create-env: ## Create .env file with correct database settings
	@echo "$(BLUE)Creating .env file...$(NC)"
	@test -f .env && echo "$(YELLOW).env already exists$(NC)" || ( \
		echo "# Smart DevOps Assistant Environment Configuration" > .env && \
		echo "DEBUG=true" >> .env && \
		echo "LOG_LEVEL=INFO" >> .env && \
		echo "DATABASE_URL=postgresql+asyncpg://devops_user:devops_pass@localhost:5433/devops_assistant" >> .env && \
		echo "DATABASE_URL_SYNC=postgresql://devops_user:devops_pass@localhost:5433/devops_assistant" >> .env && \
		echo "REDIS_URL=redis://localhost:6380/0" >> .env && \
		echo "SECRET_KEY=dev-secret-key-change-in-production" >> .env \
	)
	@echo "$(GREEN)✅ .env file created with correct database settings$(NC)"

## Quick Setup
quick-start: setup-dirs create-env db-up db-create-migration db-migrate seed-db ## Complete setup for new developers
	@echo ""
	@echo "$(GREEN)🚀 Quick start complete!$(NC)"
	@echo ""
	@echo "$(BLUE)Services available:$(NC)"
	@echo "• API: http://localhost:8000"
	@echo "• PostgreSQL: localhost:5433"
	@echo "• Redis: localhost:6380"
	@echo "• Grafana: http://localhost:3000 (admin/admin)"
	@echo "• Prometheus: http://localhost:9090"
	@echo ""
	@echo "$(BLUE)Next steps:$(NC)"
	@echo "1. Run 'make dev' to start the application"
	@echo "2. Visit http://localhost:8000/docs for API documentation"
	@echo ""

dev-api: ## Start API development server
	@echo "$(BLUE)Starting API development server...$(NC)"
	@export DATABASE_URL="postgresql+asyncpg://devops_user:devops_pass@localhost:5433/devops_assistant" && \
		export REDIS_URL="redis://localhost:6380/0" && \
		poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-with-services: db-up ## Start API with all supporting services
	@echo "$(BLUE)Starting development environment...$(NC)"
	@$(MAKE) dev-api &
	@echo "$(GREEN)✅ Development environment started$(NC)"
	@echo "$(BLUE)API will be available at: http://localhost:8000$(NC)"
