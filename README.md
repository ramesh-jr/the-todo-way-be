# The Todo Way - Backend

REST API for **The Todo Way** — a personal Life Command Center (capture → clarify → engage → review). Domains, priorities, routines, items, calendar sync, reviews, and data-trust endpoints.

## Tech Stack

- **Python 3.13** + **FastAPI**
- **SQLAlchemy 2.0** (async) + **Alembic**
- **PostgreSQL 16**
- **Pydantic v2**, JWT auth (`bcrypt` + `python-jose`)
- **Uvicorn** (local) / **Mangum** (AWS Lambda)
- **pywebpush** (optional Web Push), **httpx** (calendar OAuth)

## Getting Started

### Prerequisites

- Python 3.13+, [uv](https://docs.astral.sh/uv/), PostgreSQL 16 (or Docker)

### Local Development

```bash
uv sync
cp .env.example .env
# Edit .env — at minimum set JWT_SECRET and DATABASE_URL

docker compose up db -d
make migrate
make dev
# API: http://localhost:8000  ·  Docs: http://localhost:8000/docs
```

First request: `POST /api/v1/auth/setup` with `{ "username", "password", "recovery_email?" }`.

### Jobs

```bash
make reminders      # deliver due Web Push reminders
make backup         # write JSON snapshots to backups/
make import-backup ACCOUNT=alice FILE=backups/backup-….json
```

### Tests

```bash
make test
```

## Project Structure

```
app/
  api/v1/routes/   # thin handlers → services
  services/        # business logic
  models/          # SQLAlchemy ORM
  schemas/         # Pydantic I/O
  core/            # config, JWT, deps
scripts/           # reminders, backup, import
alembic/
docs/
```

## Documentation

- [Backend LLD](docs/lld-backend.md)
- [Data trust](docs/data-trust.md)
- [v3 plan](docs/plans/v3-life-command-center.md)
- [Pending human ops (OAuth, VAPID, email, deploy)](docs/ops-pending.md)
