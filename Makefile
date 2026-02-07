.PHONY: help dev db migrate test lint format check clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# === Development ===

dev: ## Start dev server (uvicorn with reload)
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

db: ## Start PostgreSQL in Docker
	docker compose up db -d

dev-docker: ## Start backend + DB in Docker
	docker compose up backend db

dev-full: ## Start full stack (DB + Backend + Frontend) in Docker
	docker compose --profile full up

# === Database ===

migrate: ## Run all pending migrations
	uv run alembic upgrade head

migrate-new: ## Create a new migration (usage: make migrate-new MSG="add xyz")
	uv run alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Rollback last migration
	uv run alembic downgrade -1

# === Quality ===

lint: ## Run linter (ruff)
	uv run ruff check .

format: ## Format code (ruff)
	uv run ruff format .

typecheck: ## Run type checker (mypy)
	uv run mypy app/

test: ## Run tests
	uv run pytest -v

check: lint typecheck test ## Run all checks (lint + typecheck + tests)

# === Cleanup ===

clean: ## Remove caches and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ dist/ build/ *.egg-info/
