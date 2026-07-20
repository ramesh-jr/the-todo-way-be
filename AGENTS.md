# The Todo Way - Backend

## Project Overview

REST API for a personal Life Command Center. Single-user JWT auth. Domains, standards, reflections, priorities, routines, items (capture/clarify/schedule), calendar sync (Google/Outlook), reviews, nudges, export/backup, web-push, account recovery.

## Tech Stack

- Python 3.13, FastAPI
- SQLAlchemy 2.0 (async via asyncpg), Alembic
- PostgreSQL 16
- Pydantic v2
- JWT: python-jose + bcrypt
- ASGI: Uvicorn (local), Mangum (AWS Lambda)
- pywebpush, httpx, cryptography (Fernet for OAuth tokens)
- pytest + pytest-asyncio + httpx; Ruff; mypy; uv

## Architecture

```
Routes (thin) -> Services (business logic) -> Models/DB
```

- **Routes** (`app/api/v1/routes/`): Pydantic in/out, delegate to services, return `ApiResponse`.
- **Services** (`app/services/`): All queries and business rules.
- **Models** / **Schemas** / **Core** as usual.

Routes NEVER import SQLAlchemy directly. Services NEVER return HTTP responses.

## API Response Format

```json
{"data": ..., "error": null, "meta": {"total": 42, "page": 1, "per_page": 50, "total_pages": 1}}
```

## Key Endpoint Groups

- Auth: `/api/v1/auth/setup`, `login`, `recovery/*`
- Items / capture / clarify / schedule / complete
- Domains, standards, reflections, priorities, routines
- Calendar: connect / callback / sync
- Reviews, nudges, push, data export/backup

## Jobs

- `scripts/deliver_reminders.py` (`make reminders`)
- `scripts/backup_all.py` (`make backup`)
- `scripts/import_backup.py` (`make import-backup ACCOUNT=… FILE=…`)

## Environment

`DATABASE_URL`, `JWT_SECRET`, `ENVIRONMENT`, `CORS_ORIGINS`, `APP_BASE_URL`, `FRONTEND_BASE_URL`, `ENCRYPTION_KEY`, `VAPID_*`, `GOOGLE_*`, `MS_*`, optional `SMTP_*`. See `.env.example` and `docs/ops-pending.md`.

## Conventions

- Async throughout; Google-style docstrings on public functions; mypy strict; Ruff; Conventional Commits.

## Reference Docs

- `docs/lld-backend.md`, `docs/data-trust.md`, `docs/ops-pending.md`
- `docs/plans/v3-life-command-center.md`
