# The Todo Way - Backend

REST API backend for a personal productivity app (Todoist-like). Built with Python, FastAPI, and PostgreSQL.

## Tech Stack

- **Python 3.13** + **FastAPI**
- **SQLAlchemy 2.0** (async) + **Alembic** (migrations)
- **PostgreSQL 16**
- **Pydantic v2** (validation + settings)
- **JWT** auth (python-jose + passlib)
- **Uvicorn** (local dev) / **Mangum** (AWS Lambda)

## Getting Started

### Prerequisites

- Python 3.13+
- PostgreSQL 16 (or Docker)
- [uv](https://docs.astral.sh/uv/) (Python package manager)

### Local Development

```bash
# Install dependencies
uv sync

# Copy env file
cp .env.example .env

# Start PostgreSQL (Docker)
docker compose up db -d

# Run migrations
uv run alembic upgrade head

# Start dev server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Compose (Full Stack)

```bash
# Start everything (DB + Backend + Frontend)
docker compose up

# Backend available at http://localhost:8000
# API docs at http://localhost:8000/docs (Swagger) or /redoc
```

### Running Tests

```bash
uv run pytest
```

## Project Structure

```
app/
  api/v1/routes/       # FastAPI route handlers
  core/                # Config, security, dependencies
  models/              # SQLAlchemy ORM models
  schemas/             # Pydantic request/response schemas
  services/            # Business logic layer
  db/                  # Database session + base
  main.py              # FastAPI app + Mangum handler
alembic/               # Database migrations
tests/                 # pytest tests
docker-compose.yml     # Full local stack
Dockerfile
pyproject.toml
Makefile
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
