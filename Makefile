.PHONY: help install dev build up down test test-unit test-integration test-e2e lint format clean logs ps reset

.DEFAULT_GOAL := help

# ---------- Help ----------
help: ## Show this help message
	@echo "AI Course Video Generator - Makefile"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*?##/ { printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# ---------- Setup ----------
install: ## Install all dependencies (frontend + backend)
	@echo "[1/2] Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "[2/2] Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Dependencies installed."

dev: ## Start development stack with docker compose
	docker compose up --build

up: ## Start services (rebuild if needed)
	docker compose up -d --build

build: ## Build all docker images
	docker compose build

down: ## Stop and remove containers
	docker compose down

logs: ## Follow logs from all services
	docker compose logs -f

ps: ## Show service status
	docker compose ps

# ---------- Backend dev ----------
backend-dev: ## Run backend dev server locally (no docker)
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ---------- Frontend dev ----------
frontend-dev: ## Run frontend dev server locally (no docker)
	cd frontend && npm run dev

# ---------- Testing ----------
test: test-unit test-integration ## Run all tests except E2E

test-unit: ## Run backend unit tests
	cd backend && python -m pytest tests/unit -v --cov=app --cov-report=term-missing

test-integration: ## Run backend integration tests
	cd backend && python -m pytest tests/integration -v

test-e2e: ## Run E2E tests with Playwright
	cd frontend && npx playwright test

test-backend: ## Run all backend tests
	cd backend && python -m pytest tests -v --cov=app --cov-report=term-missing

test-frontend: ## Run frontend unit tests
	cd frontend && npm run test

# ---------- Quality ----------
lint: ## Run linters (backend + frontend)
	@echo "[1/2] Backend linting..."
	cd backend && python -m ruff check app/ tests/ || echo "ruff not installed, skipping"
	@echo "[2/2] Frontend linting..."
	cd frontend && npm run lint || echo "eslint skipped"

format: ## Format code (backend + frontend)
	@echo "[1/2] Backend formatting..."
	cd backend && python -m ruff format app/ tests/ || echo "ruff not installed, skipping"
	@echo "[2/2] Frontend formatting..."
	cd frontend && npm run format || echo "prettier skipped"

# ---------- Database ----------
migrations: ## Create new Alembic migration
	cd backend && alembic revision --autogenerate -m "$(msg)"

migrate: ## Apply Alembic migrations
	cd backend && alembic upgrade head

# ---------- Clean ----------
clean: ## Remove __pycache__, node_modules, and build artifacts
	@echo "Cleaning backend..."
	cd backend && find . -type d -name "__pycache__" -exec rm -rf {} + 2>nul || true
	cd backend && find . -type f -name "*.pyc" -delete 2>nul || true
	@echo "Cleaning frontend..."
	cd frontend && rm -rf dist node_modules/.vite 2>nul || true
	@echo "Cleaning pytest cache..."
	cd backend && rm -rf .pytest_cache .coverage htmlcov 2>nul || true
	@echo "Clean complete."

reset: down ## Reset everything: containers, volumes, caches
	docker compose down -v
	@echo "All services stopped, volumes removed."
