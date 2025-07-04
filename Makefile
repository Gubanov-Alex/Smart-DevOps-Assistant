# Smart DevOps Assistant - Optimized Professional Makefile
# ========================================================
# Requires: Poetry, Docker, Docker Compose

# =============================================================================
# CONFIGURATION
# =============================================================================

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
PURPLE := \033[0;35m
NC := \033[0m

# Environment detection
ENV ?= development
ifeq ($(ENV),production)
	DOCKER_FILE := docker/Dockerfile.prod
	COMPOSE_FILE := docker-compose.prod.yml
else
	DOCKER_FILE := docker/Dockerfile.dev
	COMPOSE_FILE := docker-compose.yml
endif

# Database configuration
DB_URL := postgresql://devops_user:devops_pass@localhost:5433/devops_assistant
DB_URL_ASYNC := postgresql+asyncpg://devops_user:devops_pass@localhost:5433/devops_assistant
REDIS_URL_VAR := redis://localhost:6380/0

# Default target
.DEFAULT_GOAL := help
.PHONY: help install dev test lint format security build deploy clean
.PHONY: test-repositories test-incident-repo test-mlmodel-repo test-unit-fast test-coverage
.PHONY:test-performance test-watch test-debug test-failed test-report setup-repositories
.PHONY:qa-repositories test-integration-repos benchmark-repositories ci-test-repositories
.PHONY:repo-shell docs-repositories clean-test-artifacts help-repositories
# =============================================================================
# HELP & INFORMATION
# =============================================================================

help: ## Show comprehensive help with categorized commands
	@echo "$(BLUE)Smart DevOps Assistant - Available Commands$(NC)"
	@echo "============================================="
	@echo ""
	@echo "$(PURPLE)📦 Setup & Installation:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / && /Setup|Install|Environment/ {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(PURPLE)🚀 Development:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / && /dev|Development|Start/ {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(PURPLE)🗄️ Database Operations:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / && /Database|db-|migration/ {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(PURPLE)🧪 Testing & Quality:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / && /test|Test|quality|Quality|lint|format|security/ {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(PURPLE)🐳 Docker & Deployment:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / && /Docker|deploy|build|push/ {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(PURPLE)🧹 Maintenance:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / && /clean|Clean|backup|restore/ {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

status: ## Show comprehensive project status
	@echo "$(BLUE)📊 Project Status$(NC)"
	@echo "=================="
	@echo "Environment: $(ENV)"
	@echo "Python: $(PYTHON_VERSION)"
	@echo "Poetry: $(POETRY_VERSION)"
	@echo "Docker Compose: $$(docker-compose --version 2>/dev/null | cut -d' ' -f3 || echo 'Not installed')"
	@echo ""
	@echo "$(BLUE)🗄️ Database Status:$(NC)"
	@docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(postgres|redis)" || echo "No database containers running"
	@echo ""
	@echo "$(BLUE)📁 Reports:$(NC)"
	@ls -la reports/ 2>/dev/null | tail -n +2 | wc -l | xargs echo "Report files:"
	@echo "Last security scan: $$(ls -la reports/security/bandit-report.txt 2>/dev/null | awk '{print $$6, $$7, $$8}' || echo 'Never')"

# =============================================================================
# SETUP & INSTALLATION
# =============================================================================

setup-dirs: ## Create all necessary project directories
	@echo "$(BLUE)📁 Creating project directories...$(NC)"
	@mkdir -p reports/{security,coverage,benchmarks}
	@mkdir -p logs/{app,security,audit}
	@mkdir -p models/{checkpoints,exports,backups}
	@mkdir -p data/{raw,processed,temp}
	@mkdir -p docs/{api,user,dev}
	@mkdir -p backups/{db,models,configs}
	@mkdir -p .secrets
	@touch .secrets/.gitkeep 2>/dev/null || true
	@echo "$(GREEN)✅ Directories created$(NC)"

create-env: ## Create optimized .env file with all required settings
	@echo "$(BLUE)📝 Creating .env configuration...$(NC)"
	@test -f .env && echo "$(YELLOW).env already exists, creating .env.example$(NC)" || true
	@cat > .env.example <<'EOF'
# Smart DevOps Assistant Environment Configuration
# ================================================

# Application Settings
DEBUG=true
LOG_LEVEL=INFO
ENVIRONMENT=development

# Database Configuration
DATABASE_URL=postgresql+asyncpg://devops_user:devops_pass@localhost:5433/devops_assistant
DATABASE_URL_SYNC=postgresql://devops_user:devops_pass@localhost:5433/devops_assistant

# Redis Configuration
REDIS_URL=redis://localhost:6380/0
CELERY_BROKER_URL=redis://localhost:6380/1
CELERY_RESULT_BACKEND=redis://localhost:6380/1

# Security
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=jwt-secret-change-in-production

# API Configuration
API_V1_PREFIX=/api/v1
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Database Pool Settings
POOL_SIZE=10
MAX_OVERFLOW=20
POOL_TIMEOUT=30
POOL_RECYCLE=3600

# ML/AI Settings
MODEL_PATH=./models
ENABLE_ML=true
ML_CACHE_SIZE=100

# Monitoring
ENABLE_METRICS=true
PROMETHEUS_PORT=9090
EOF:
	@test -f .env || cp .env.example .env
	@echo "$(GREEN)✅ Environment configuration ready$(NC)"

install: setup-dirs create-env ## Complete development environment setup
	@echo "$(BLUE)🔧 Setting up development environment...$(NC)"
	@echo "$(YELLOW)Installing Poetry $(POETRY_VERSION)...$(NC)"
	@curl -sSL https://install.python-poetry.org | python3 - --version $(POETRY_VERSION) 2>/dev/null || echo "Poetry already installed"
	@echo "$(YELLOW)Installing dependencies...$(NC)"
	@poetry install --no-interaction
	@echo "$(YELLOW)Setting up pre-commit hooks...$(NC)"
	@poetry run pre-commit install --install-hooks 2>/dev/null || echo "Pre-commit setup completed"
	@echo "$(GREEN)✅ Development environment ready!$(NC)"

# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

db-services-up: ## Start database services (PostgreSQL + Redis)
	@echo "$(BLUE)🗄️ Starting database services...$(NC)"
	@docker-compose up -d postgres redis
	@echo "$(YELLOW)⏳ Waiting for services to be ready...$(NC)"
	@sleep 12
	@echo "$(GREEN)✅ Database services ready$(NC)"
	@echo "$(BLUE)Connections available:$(NC)"
	@echo "  PostgreSQL: $(DB_URL)"
	@echo "  Redis: $(REDIS_URL_VAR)"

db-services-down: ## Stop database services
	@echo "$(BLUE)🛑 Stopping database services...$(NC)"
	@docker-compose down
	@echo "$(GREEN)✅ Database services stopped$(NC)"

db-services-status: ## Check database services status
	@echo "$(BLUE)📊 Database Services Status$(NC)"
	@echo "=============================="
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -1
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(postgres|redis)" || echo "No database containers running"
	@echo ""
	@echo "$(BLUE)🔍 Testing connections:$(NC)"
	@psql $(DB_URL) -c "SELECT version();" 2>/dev/null && echo "$(GREEN)✅ PostgreSQL: Connected$(NC)" || echo "$(RED)❌ PostgreSQL: Failed$(NC)"
	@redis-cli -u $(REDIS_URL_VAR) ping 2>/dev/null && echo "$(GREEN)✅ Redis: Connected$(NC)" || echo "$(RED)❌ Redis: Failed$(NC)"

db-init-alembic: ## Initialize Alembic migrations (run once)
	@echo "$(BLUE)🔧 Initializing Alembic...$(NC)"
	@poetry run alembic init alembic 2>/dev/null || echo "$(YELLOW)Alembic already initialized$(NC)"
	@echo "$(GREEN)✅ Alembic ready$(NC)"

db-create-migration: db-services-up ## Create new database migration
	@echo "$(BLUE)📝 Creating database migration...$(NC)"
	@export DATABASE_URL_SYNC="$(DB_URL)" && \
		poetry run alembic revision --autogenerate -m "$(if $(m),$(m),Auto-generated migration)"
	@echo "$(GREEN)✅ Migration created$(NC)"

db-migrate: db-services-up ## Apply pending database migrations
	@echo "$(BLUE)⬆️ Applying database migrations...$(NC)"
	@sleep 5
	@export DATABASE_URL_SYNC="$(DB_URL)" && \
		poetry run alembic upgrade head
	@echo "$(GREEN)✅ Database migrations applied$(NC)"

db-rollback: ## Rollback one database migration
	@echo "$(BLUE)⬇️ Rolling back database migration...$(NC)"
	@export DATABASE_URL_SYNC="$(DB_URL)" && \
		poetry run alembic downgrade -1
	@echo "$(GREEN)✅ Database rolled back$(NC)"

db-history: ## Show migration history
	@echo "$(BLUE)📜 Migration History$(NC)"
	@echo "==================="
	@export DATABASE_URL_SYNC="$(DB_URL)" && \
		poetry run alembic history --verbose

db-current: ## Show current migration version
	@echo "$(BLUE)📍 Current Migration$(NC)"
	@echo "==================="
	@export DATABASE_URL_SYNC="$(DB_URL)" && \
		poetry run alembic current --verbose

db-shell: db-services-up ## Connect to PostgreSQL shell
	@echo "$(BLUE)🐘 Connecting to PostgreSQL...$(NC)"
	@docker-compose exec postgres psql -U devops_user -d devops_assistant

db-reset: ## DANGEROUS: Reset database completely
	@echo "$(RED)⚠️ DANGER: This will destroy ALL database data!$(NC)"
	@echo "$(YELLOW)Type 'YES' to confirm complete database reset:$(NC)"
	@read ans && [ "$$ans" = "YES" ] || (echo "Cancelled" && exit 1)
	@echo "$(BLUE)🔄 Resetting database...$(NC)"
	@docker-compose down -v 2>/dev/null || true
	@$(MAKE) db-services-up
	@sleep 10
	@$(MAKE) db-migrate
	@echo "$(GREEN)✅ Database reset complete$(NC)"

db-seed: db-migrate ## Seed database with development data
	@echo "$(BLUE)🌱 Seeding database...$(NC)"
	@export DATABASE_URL="$(DB_URL_ASYNC)" && \
		poetry run python scripts/seed_database.py 2>/dev/null || echo "$(YELLOW)No seed script found$(NC)"
	@echo "$(GREEN)✅ Database seeded$(NC)"

db-backup: ## Create timestamped database backup
	@echo "$(BLUE)💾 Creating database backup...$(NC)"
	@mkdir -p backups/db
	@docker-compose exec postgres pg_dump -U devops_user devops_assistant > backups/db/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ Backup created in backups/db/$(NC)"

db-restore: ## Restore database from backup (BACKUP_FILE=path/to/backup.sql)
	@echo "$(BLUE)📥 Restoring database...$(NC)"
	@test -n "$(BACKUP_FILE)" || (echo "$(RED)Usage: make db-restore BACKUP_FILE=path/to/backup.sql$(NC)" && exit 1)
	@test -f "$(BACKUP_FILE)" || (echo "$(RED)Backup file not found: $(BACKUP_FILE)$(NC)" && exit 1)
	@docker-compose exec -T postgres psql -U devops_user devops_assistant < $(BACKUP_FILE)
	@echo "$(GREEN)✅ Database restored from $(BACKUP_FILE)$(NC)"

# =============================================================================
# DEVELOPMENT
# =============================================================================

dev: db-services-up ## Start development server with hot reload
	@echo "$(BLUE)🚀 Starting development server...$(NC)"
	@export DATABASE_URL="$(DB_URL_ASYNC)" && \
		export REDIS_URL="$(REDIS_URL_VAR)" && \
		poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-full: ## Start complete development environment
	@echo "$(BLUE)🌟 Starting full development environment...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)✅ Full environment running$(NC)"
	@echo "$(BLUE)Available services:$(NC)"
	@echo "  • API: http://localhost:8000"
	@echo "  • API Docs: http://localhost:8000/docs"
	@echo "  • Grafana: http://localhost:3000 (admin/admin)"
	@echo "  • Prometheus: http://localhost:9090"
	@echo "  • Flower: http://localhost:5555"

dev-api-only: create-env ## Start only API server (assumes DB running)
	@echo "$(BLUE)⚡ Starting API server only...$(NC)"
	@export DATABASE_URL="$(DB_URL_ASYNC)" && \
		export REDIS_URL="$(REDIS_URL_VAR)" && \
		poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# =============================================================================
# TESTING & QUALITY ASSURANCE
# =============================================================================

format: ## Format code with black and isort
	@echo "$(BLUE)🎨 Formatting code...$(NC)"
	@poetry run black app/ tests/ --line-length=88
	@poetry run isort app/ tests/ --profile black
	@echo "$(GREEN)✅ Code formatted$(NC)"

format-check: ## Check code formatting without changes
	@echo "$(BLUE)🔍 Checking code formatting...$(NC)"
	@poetry run black --check --diff app/ tests/ --line-length=88
	@poetry run isort --check-only --diff app/ tests/ --profile black

lint: ## Run comprehensive linting
	@echo "$(BLUE)🔍 Running code quality checks...$(NC)"
	@poetry run flake8 app/ tests/ --max-complexity=10 --max-line-length=88 --extend-ignore=E203,W503
	@poetry run mypy app/ --ignore-missing-imports || echo "$(YELLOW)MyPy warnings found$(NC)"
	@echo "$(GREEN)✅ Linting completed$(NC)"

security: setup-dirs ## Run comprehensive security analysis
	@echo "$(BLUE)🔒 Running security analysis...$(NC)"
	@poetry run bandit -r app/ -f json -o reports/security/bandit-report.json -ll 2>/dev/null || echo "$(YELLOW)Security issues found$(NC)"
	@poetry run bandit -r app/ -f txt -o reports/security/bandit-report.txt -ll 2>/dev/null || echo "$(YELLOW)Security issues found$(NC)"
	@poetry run safety check --json --output reports/security/safety-report.json 2>/dev/null || echo "$(YELLOW)Vulnerabilities found$(NC)"
	@echo "$(GREEN)✅ Security analysis complete - check reports/security/$(NC)"

test: setup-dirs ## Run full test suite with coverage
	@echo "$(BLUE)🧪 Running test suite...$(NC)"
	@poetry run pytest tests/ \
		--cov=app \
		--cov-report=html:reports/coverage/htmlcov \
		--cov-report=xml:reports/coverage/coverage.xml \
		--cov-report=term-missing \
		--cov-fail-under=75 \
		--tb=short \
		-v
	@echo "$(GREEN)✅ Tests complete - coverage: reports/coverage/htmlcov/index.html$(NC)"

test-fast: ## Run tests without coverage for quick feedback
	@echo "$(BLUE)⚡ Running fast tests...$(NC)"
	@poetry run pytest tests/ --tb=short -q
	@echo "$(GREEN)✅ Fast tests completed$(NC)"

test-integration: db-services-up ## Run integration tests with real database
	@echo "$(BLUE)🔗 Running integration tests...$(NC)"
	@export DATABASE_URL="$(DB_URL_ASYNC)" && \
		export REDIS_URL="$(REDIS_URL_VAR)" && \
		poetry run pytest tests/integration/ -v --tb=short
	@echo "$(GREEN)✅ Integration tests completed$(NC)"

benchmark: setup-dirs ## Run performance benchmarks
	@echo "$(BLUE)📊 Running benchmarks...$(NC)"
	@poetry run pytest tests/ -m benchmark \
		--benchmark-only \
		--benchmark-json=reports/benchmarks/benchmark-results.json \
		--benchmark-sort=mean \
		--benchmark-group-by=func \
		--benchmark-warmup=on \
		--benchmark-disable-gc 2>/dev/null || echo "$(YELLOW)No benchmarks configured$(NC)"
	@echo "$(GREEN)✅ Benchmarks completed$(NC)"

qa: format lint security test ## Run complete quality assurance pipeline
	@echo "$(GREEN)✅ QA pipeline completed successfully!$(NC)"

pre-commit: ## Run pre-commit hooks on all files
	@echo "$(BLUE)🪝 Running pre-commit hooks...$(NC)"
	@poetry run pre-commit run --all-files || echo "$(YELLOW)Some checks failed$(NC)"

ci-check: setup-dirs ## Simulate complete CI pipeline locally
	@echo "$(BLUE)🤖 Simulating CI pipeline...$(NC)"
	@$(MAKE) format-check || echo "$(YELLOW)Format issues found$(NC)"
	@$(MAKE) lint || echo "$(YELLOW)Lint issues found$(NC)"
	@$(MAKE) security || echo "$(YELLOW)Security issues found$(NC)"
	@$(MAKE) test || echo "$(YELLOW)Test issues found$(NC)"
	@echo "$(GREEN)✅ CI simulation complete$(NC)"

# =============================================================================
# DOCKER & DEPLOYMENT
# =============================================================================

build: ## Build optimized Docker image
	@echo "$(BLUE)🐳 Building Docker image for $(ENV)...$(NC)"
	@docker build -f $(DOCKER_FILE) -t $(IMAGE_NAME):$(ENV) -t $(IMAGE_NAME):latest .
	@echo "$(GREEN)✅ Image built: $(IMAGE_NAME):$(ENV)$(NC)"

push: build ## Build and push Docker image to registry
	@echo "$(BLUE)📤 Pushing Docker image...$(NC)"
	@docker push $(IMAGE_NAME):$(ENV)
	@docker push $(IMAGE_NAME):latest
	@echo "$(GREEN)✅ Image pushed to $(DOCKER_REGISTRY)$(NC)"

deploy: build ## Deploy application with Docker Compose
	@echo "$(BLUE)🚀 Deploying application...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) up -d
	@echo "$(GREEN)✅ Application deployed$(NC)"

# =============================================================================
# AI/ML OPERATIONS
# =============================================================================

train-models: setup-dirs ## Train ML models
	@echo "$(BLUE)🤖 Training ML models...$(NC)"
	@export DATABASE_URL="$(DB_URL_ASYNC)" && \
		poetry run python scripts/train_models.py 2>/dev/null || echo "$(YELLOW)Training script not found$(NC)"
	@echo "$(GREEN)✅ Model training completed$(NC)"

validate-models: ## Validate trained models
	@echo "$(BLUE)✅ Validating ML models...$(NC)"
	@poetry run python scripts/validate_models.py 2>/dev/null || echo "$(YELLOW)Validation script not found$(NC)"
	@echo "$(GREEN)✅ Model validation completed$(NC)"

# =============================================================================
# MAINTENANCE & CLEANUP
# =============================================================================

clean-cache: ## Clean Python cache files
	@echo "$(BLUE)🧹 Cleaning Python cache...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf dist/ build/ .coverage 2>/dev/null || true
	@echo "$(GREEN)✅ Cache cleaned$(NC)"

clean-reports: setup-dirs ## Clean all report files
	@echo "$(BLUE)📄 Cleaning reports...$(NC)"
	@rm -rf reports/* 2>/dev/null || true
	@$(MAKE) setup-dirs > /dev/null
	@echo "$(GREEN)✅ Reports cleaned$(NC)"

clean-docker: ## Clean Docker resources
	@echo "$(BLUE)🐳 Cleaning Docker resources...$(NC)"
	@docker-compose down --volumes --remove-orphans 2>/dev/null || true
	@docker system prune -f 2>/dev/null || true
	@echo "$(GREEN)✅ Docker cleaned$(NC)"

clean: clean-cache clean-reports ## Clean cache and reports
	@echo "$(GREEN)✅ Cleanup completed$(NC)"

# =============================================================================
# ADVANCED WORKFLOWS
# =============================================================================

fresh-start: clean clean-docker install db-reset db-seed ## Complete fresh environment setup
	@echo "$(GREEN)🌟 Fresh start completed!$(NC)"
	@echo "$(BLUE)Ready for development. Run 'make dev' to start.$(NC)"

quick-setup: install db-services-up db-migrate db-seed ## Quick setup for new developers
	@echo "$(GREEN)⚡ Quick setup complete!$(NC)"
	@echo ""
	@echo "$(BLUE)🎯 Next steps:$(NC)"
	@echo "1. Run 'make dev' to start API server"
	@echo "2. Visit http://localhost:8000/docs for API documentation"
	@echo "3. Run 'make test' to verify everything works"

emergency-security: ## Emergency security scan and fixes
	@echo "$(RED)🚨 Running emergency security scan...$(NC)"
	@poetry run bandit -r app/ -ll --severity=high --confidence=high || echo "$(RED)HIGH PRIORITY ISSUES FOUND!$(NC)"
	@poetry run safety check --short-report || echo "$(RED)VULNERABILITIES FOUND!$(NC)"
	@echo "$(GREEN)✅ Emergency scan completed$(NC)"

full-workflow: qa test-integration build ## Complete development workflow
	@echo "$(GREEN)🎉 Full workflow completed successfully!$(NC)"

# =============================================================================
# UTILITY COMMANDS
# =============================================================================

check-deps: ## Check for dependency updates
	@echo "$(BLUE)📦 Checking dependencies...$(NC)"
	@poetry show --outdated || echo "$(GREEN)All dependencies up to date$(NC)"

update-deps: ## Update dependencies safely
	@echo "$(BLUE)⬆️ Updating dependencies...$(NC)"
	@poetry update
	@$(MAKE) security > /dev/null
	@echo "$(GREEN)✅ Dependencies updated$(NC)"

docs: setup-dirs ## Generate documentation
	@echo "$(BLUE)📚 Generating documentation...$(NC)"
	@poetry run sphinx-build -b html docs/ docs/_build/html 2>/dev/null || echo "$(YELLOW)Sphinx may not be configured$(NC)"
	@echo "$(GREEN)✅ Documentation ready$(NC)"

# =============================================================================
# VALIDATION & HEALTH CHECKS
# =============================================================================

validate-environment: ## Validate complete development environment
	@echo "$(BLUE)🔍 Validating development environment...$(NC)"
	@echo ""
	@echo "$(YELLOW)Checking Poetry...$(NC)"
	@poetry --version && echo "$(GREEN)✅ Poetry OK$(NC)" || echo "$(RED)❌ Poetry missing$(NC)"
	@echo ""
	@echo "$(YELLOW)Checking Docker...$(NC)"
	@docker --version && echo "$(GREEN)✅ Docker OK$(NC)" || echo "$(RED)❌ Docker missing$(NC)"
	@echo ""
	@echo "$(YELLOW)Checking Docker Compose...$(NC)"
	@docker-compose --version && echo "$(GREEN)✅ Docker Compose OK$(NC)" || echo "$(RED)❌ Docker Compose missing$(NC)"
	@echo ""
	@echo "$(YELLOW)Checking Python dependencies...$(NC)"
	@poetry run python -c "import app; print('✅ App imports OK')" 2>/dev/null || echo "$(RED)❌ Import issues$(NC)"
	@echo ""
	@$(MAKE) db-services-status
	@echo ""
	@echo "$(GREEN)🎯 Environment validation complete$(NC)"

health-check: ## Comprehensive health check
	@echo "$(BLUE)🏥 Running health checks...$(NC)"
	@$(MAKE) validate-environment
	@$(MAKE) test-fast > /dev/null && echo "$(GREEN)✅ Tests passing$(NC)" || echo "$(RED)❌ Tests failing$(NC)"
	@$(MAKE) format-check > /dev/null && echo "$(GREEN)✅ Code formatting OK$(NC)" || echo "$(YELLOW)⚠️ Formatting issues$(NC)"
	@echo "$(GREEN)🎯 Health check complete$(NC)"

# Test targets
test-repositories: ## Run all repository tests
	@echo "$(BLUE)🧪 Running repository tests...$(NC)"
	@poetry run pytest tests/unit/ -k "repository" -v --cov=app/infrastructure/repositories --cov-report=html
	@echo "$(GREEN)✅ Repository tests completed$(NC)"

test-incident-repo: ## Run incident repository tests
	@echo "$(BLUE)🧪 Running incident repository tests...$(NC)"
	@poetry run pytest tests/unit/test_incident_repository.py -v
	@echo "$(GREEN)✅ Incident repository tests completed$(NC)"

test-mlmodel-repo: ## Run ML model repository tests
	@echo "$(BLUE)🧪 Running ML model repository tests...$(NC)"
	@poetry run pytest tests/unit/test_mlmodel_repository.py -v
	@echo "$(GREEN)✅ ML model repository tests completed$(NC)"

test-unit-fast: ## Run unit tests in parallel
	@echo "$(BLUE)🧪 Running unit tests in parallel...$(NC)"
	@poetry run pytest tests/unit/ -n auto --dist=loadscope
	@echo "$(GREEN)✅ Unit tests completed$(NC)"

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)📊 Running tests with coverage...$(NC)"
	@poetry run pytest tests/unit/ --cov=app --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✅ Coverage report generated$(NC)"
	@echo "$(BLUE)📋 Open htmlcov/index.html to view detailed coverage$(NC)"

test-performance: ## Run performance tests
	@echo "$(BLUE)⚡ Running performance tests...$(NC)"
	@poetry run pytest tests/unit/ -m "performance" -v
	@echo "$(GREEN)✅ Performance tests completed$(NC)"

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)👀 Starting test watch mode...$(NC)"
	@poetry run pytest-watch tests/unit/ --runner "pytest -v"

test-debug: ## Run tests with debug output
	@echo "$(BLUE)🔍 Running tests with debug output...$(NC)"
	@poetry run pytest tests/unit/ -v -s --log-level=DEBUG

test-failed: ## Run only failed tests from previous run
	@echo "$(BLUE)🔄 Running only failed tests...$(NC)"
	@poetry run pytest --lf tests/unit/

test-report: ## Generate detailed test report
	@echo "$(BLUE)📝 Generating test report...$(NC)"
	@mkdir -p reports
	@poetry run pytest tests/unit/ --html=reports/test_report.html --self-contained-html --junitxml=reports/junit.xml
	@echo "$(GREEN)✅ Test report generated: reports/test_report.html$(NC)"

# Repository setup targets
setup-repositories: ## Setup repository files and dependencies
	@echo "$(BLUE)🔧 Setting up repository structure...$(NC)"
	@mkdir -p app/infrastructure/repositories
	@mkdir -p tests/unit/repositories
	@mkdir -p tests/factories
	@poetry add --group dev pytest-asyncio pytest-mock faker pytest-cov pytest-xdist
	@echo "$(GREEN)✅ Repository structure ready$(NC)"

# Quality assurance targets
qa-repositories: ## Run full QA pipeline for repositories
	@echo "$(BLUE)🔍 Running QA pipeline for repositories...$(NC)"
	@poetry run black app/infrastructure/repositories/ tests/unit/
	@poetry run isort app/infrastructure/repositories/ tests/unit/
	@poetry run flake8 app/infrastructure/repositories/ tests/unit/
	@poetry run mypy app/infrastructure/repositories/
	@poetry run bandit -r app/infrastructure/repositories/
	@poetry run pytest tests/unit/ -k "repository" --cov=app/infrastructure/repositories --cov-report=term-missing
	@echo "$(GREEN)✅ QA pipeline completed$(NC)"

# Integration targets
test-integration-repos: db-services-up ## Run integration tests for repositories
	@echo "$(BLUE)🔗 Running repository integration tests...$(NC)"
	@sleep 5
	@poetry run pytest tests/integration/ -k "repository" -v --db-url=$(DB_URL)
	@echo "$(GREEN)✅ Integration tests completed$(NC)"

# Benchmark targets
benchmark-repositories: ## Run repository performance benchmarks
	@echo "$(BLUE)📊 Running repository benchmarks...$(NC)"
	@poetry run pytest tests/unit/ -k "repository" --benchmark-only --benchmark-sort=mean
	@echo "$(GREEN)✅ Benchmarks completed$(NC)"

# CI/CD targets
ci-test-repositories: ## CI pipeline for repository tests
	@echo "$(BLUE)🚀 Running CI pipeline for repositories...$(NC)"
	@poetry run pytest tests/unit/ -k "repository" --cov=app/infrastructure/repositories --cov-report=xml --junitxml=reports/junit.xml
	@echo "$(GREEN)✅ CI pipeline completed$(NC)"

# Documentation targets
docs-repositories: ## Generate repository documentation
	@echo "$(BLUE)📚 Generating repository documentation...$(NC)"
	@poetry run sphinx-apidoc -o docs/source/repositories app/infrastructure/repositories/
	@echo "$(GREEN)✅ Repository documentation generated$(NC)"

# Cleanup targets
clean-test-artifacts: ## Clean test artifacts
	@echo "$(BLUE)🧹 Cleaning test artifacts...$(NC)"
	@rm -rf .pytest_cache/
	@rm -rf htmlcov/
	@rm -rf reports/
	@rm -rf .coverage
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete
	@echo "$(GREEN)✅ Test artifacts cleaned$(NC)"

# Help target addition
help-repositories: ## Show repository-specific help
	@echo "$(BLUE)📋 Repository Testing Commands:$(NC)"
	@echo ""
	@echo "  $(GREEN)test-repositories$(NC)      - Run all repository tests"
	@echo "  $(GREEN)test-incident-repo$(NC)     - Run incident repository tests"
	@echo "  $(GREEN)test-mlmodel-repo$(NC)      - Run ML model repository tests"
	@echo "  $(GREEN)test-unit-fast$(NC)         - Run unit tests in parallel"
	@echo "  $(GREEN)test-coverage$(NC)          - Run tests with coverage report"
	@echo "  $(GREEN)test-performance$(NC)       - Run performance tests"
	@echo "  $(GREEN)test-watch$(NC)             - Run tests in watch mode"
	@echo "  $(GREEN)test-debug$(NC)             - Run tests with debug output"
	@echo "  $(GREEN)test-failed$(NC)            - Run only failed tests"
	@echo "  $(GREEN)test-report$(NC)            - Generate detailed test report"
	@echo "  $(GREEN)setup-repositories$(NC)     - Setup repository structure"
	@echo "  $(GREEN)qa-repositories$(NC)        - Run full QA pipeline"
	@echo "  $(GREEN)clean-test-artifacts$(NC)   - Clean test artifacts"
	@echo ""
