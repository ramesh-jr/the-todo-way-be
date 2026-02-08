# The Todo Way - Updated Plan (v1)

> **Version**: v1
> **Created**: 2026-02-07
> **Status**: Superseded by v2

## Changes from v0

1. **FullCalendar replaces custom calendar** -- Feasibility analysis confirmed all required features (TimeGrid views, external drag-and-drop, event resize, custom rendering) are available in the free MIT Standard edition. No premium license needed.
2. **Backend switched to Python/FastAPI** -- FastAPI with SQLAlchemy 2.0 (async), Alembic migrations, Pydantic v2 validation. Runs on Lambda via Mangum adapter.
3. **UI Design System added** -- Color palette (Indigo primary, Amber accent), Inter font, spacing/shadow tokens, priority semantic colors. All defined as CSS custom properties consumed by Tailwind + shadcn/ui.
4. **Docker Compose for local dev** -- Full stack (PostgreSQL + FastAPI + Vite) in containers. Application code uses environment variables only (DATABASE_URL, JWT_SECRET, ENVIRONMENT). Same code runs in Docker and on AWS Lambda.
5. **Plan versioning** -- Documents stored in docs/plans/ with version numbers and timestamps.

## Tech Stack (v1)

### Frontend
- React 19, TypeScript, Vite 6
- Tailwind CSS 4, shadcn/ui
- FullCalendar v6 (MIT): timegrid, daygrid, interaction plugins
- Zustand, React Router v7, React Hook Form + Zod
- Lucide React icons, Inter font

### Backend
- Python 3.13, FastAPI
- SQLAlchemy 2.0 (async), Alembic, Pydantic v2
- PostgreSQL 16, JWT (python-jose), passlib[bcrypt]
- Uvicorn (local), Mangum (Lambda)
- Ruff, mypy, pytest

### Infrastructure
- AWS: Lambda + API Gateway v2 + Aurora Serverless v2 + S3/CloudFront
- IaC: AWS CDK v2 (Python)
- CI/CD: GitHub Actions
- Local: Docker Compose

## What Changed in v2

- Frontend-first approach: build entire FE with static JSON dummy data before building backend
- Data provider abstraction layer for clean API swap
- Reordered implementation phases
