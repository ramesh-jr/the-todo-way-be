# The Todo Way - Backend

## Project Overview

REST API backend for a Todoist-like personal productivity app. Single-user, JWT auth, Python/FastAPI. Serves the React frontend with CRUD for todos, sections, subsections, and labels.

## Tech Stack

- Python 3.13, FastAPI
- SQLAlchemy 2.0 (async via asyncpg), Alembic (migrations)
- PostgreSQL 16
- Pydantic v2 (validation, settings)
- JWT auth: python-jose + passlib[bcrypt]
- ASGI: Uvicorn (local), Mangum (AWS Lambda)
- Testing: pytest + pytest-asyncio + httpx
- Linting: Ruff (format + lint), mypy (type checking)
- Dependency mgmt: uv + pyproject.toml

## Architecture

**Layered structure** -- strict separation, no cross-layer imports:

```
Routes (thin) -> Services (business logic) -> Models/DB (data access)
```

- **Routes** (`app/api/v1/routes/`): FastAPI route handlers. Validate input via Pydantic, delegate to services, return ApiResponse.
- **Services** (`app/services/`): Business logic. Receive DB session, operate on models. All queries live here.
- **Models** (`app/models/`): SQLAlchemy ORM models. Define tables, relationships, indexes.
- **Schemas** (`app/schemas/`): Pydantic request/response models. Validate all input/output.
- **Core** (`app/core/`): Config (env vars), security (JWT, password hashing), dependencies (get_db, get_current_user).

Routes NEVER import SQLAlchemy directly. Services NEVER return HTTP responses.

## API Response Format

All endpoints return:
```json
{"data": ..., "error": null, "meta": {"total": 42, "page": 1, "per_page": 50, "total_pages": 1}}
```
Error responses: `{"data": null, "error": "message", "meta": null}`

## Key Endpoints

- `POST /api/v1/auth/setup` (first-time), `POST /api/v1/auth/login`
- `GET/POST /api/v1/todos`, `GET/PUT/DELETE /api/v1/todos/{id}`
- `PATCH /api/v1/todos/{id}/complete`, `PATCH /api/v1/todos/{id}/schedule`
- `GET/POST /api/v1/sections`, `PUT/DELETE /api/v1/sections/{id}`
- `POST /api/v1/sections/{id}/subsections`, `PUT/DELETE /api/v1/subsections/{id}`
- `GET/POST /api/v1/labels`, `PUT/DELETE /api/v1/labels/{id}`

## Environment Abstraction

App reads config from env vars via Pydantic `BaseSettings`. Same code runs in Docker (Uvicorn) and AWS (Mangum/Lambda). Key vars: `DATABASE_URL`, `JWT_SECRET`, `ENVIRONMENT` (local|staging|production), `CORS_ORIGINS`.

## File Naming

- All Python files: snake_case (`todo_service.py`, `todo_routes.py`)
- Classes: PascalCase (`TodoService`, `TodoCreate`)
- Functions: snake_case (`get_todos`, `create_todo`)
- Constants: UPPER_SNAKE_CASE (`MAX_DURATION_MINUTES`)

## Conventions

- Async throughout (async def routes, async SQLAlchemy sessions)
- All public functions have Google-style docstrings
- Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`
- Type hints on all functions. mypy strict mode.
- Ruff for formatting + linting (replaces black/isort/flake8).

## Reference Docs

- `docs/lld-backend.md` -- Backend LLD: DB schema, Pydantic schemas, API contracts, service layer, auth flow
- `docs/plans/` -- Versioned project plans (v0, v1, v2) -- shared across FE and BE repos
