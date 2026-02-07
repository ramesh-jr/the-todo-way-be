# Contributing to The Todo Way (Backend)

## Development Setup

1. Install Python 3.13+ and [uv](https://docs.astral.sh/uv/)
2. Clone the repo and install dependencies:
   ```bash
   uv sync
   cp .env.example .env
   ```
3. Start PostgreSQL:
   ```bash
   docker compose up db -d
   ```
4. Run migrations:
   ```bash
   uv run alembic upgrade head
   ```
5. Start the dev server:
   ```bash
   uv run uvicorn app.main:app --reload --port 8000
   ```

## Code Quality

- **Format + Lint**: `uv run ruff check . && uv run ruff format .`
- **Type check**: `uv run mypy app/`
- **Test**: `uv run pytest`
- **All checks**: `make check`

## Architecture

Follow the layered architecture strictly:
```
Routes -> Services -> Models/DB
```
See `.cursor/rules/architecture.mdc` for details.

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):
- `feat: add todo filtering by label`
- `fix: handle null duration in schedule endpoint`
- `chore: update dependencies`
- `docs: add API endpoint documentation`
- `refactor: extract pagination logic to helper`
- `test: add tests for section CRUD`

## Branch Naming

- `feat/todo-crud-api`
- `fix/null-duration-handling`
- `chore/update-deps`

## Pull Requests

- One feature/fix per PR
- Include tests for new functionality
- All checks must pass (ruff, mypy, pytest)
