# The Todo Way - Backend Build Guide

> **Purpose**: Copy-paste ready conversation prompts for each build step. Open a new Cursor conversation, paste the prompt, and the AI has everything it needs.
> **Created**: 2026-02-07

---

## How to Use

1. Open `/Users/ramesh.subramanian/Documents/Development/Github/the-todo-way-be` as your Cursor workspace
2. Start a new chat (Cmd+L)
3. Copy-paste the prompt for the current task
4. The AI will auto-receive `.cursor/rules/*.mdc` files and read `AGENTS.md` + `docs/lld-backend.md`
5. After completion, verify the commit and move to the next task

---

## BE-1: FastAPI App Setup

```
Read AGENTS.md and docs/lld-backend.md Sections 5, 6, 7. Then do BE-1:

1. Implement app/core/config.py -- Pydantic BaseSettings with DATABASE_URL, JWT_SECRET, 
   JWT_ALGORITHM, JWT_EXPIRY_DAYS, ENVIRONMENT, CORS_ORIGINS per Section 5.
2. Implement app/core/exceptions.py -- AppException, NotFoundException, ConflictException 
   per Section 6.
3. Implement app/db/session.py -- async engine, AsyncSessionLocal, get_db dependency 
   per Section 7.
4. Implement app/schemas/response.py -- PaginationMeta and ApiResponse[T] generic wrapper 
   per Section 2.1.
5. Implement app/api/v1/__init__.py -- Create v1 APIRouter, include sub-routers (empty 
   for now, just the aggregation).
6. Implement app/main.py -- Create FastAPI app, add CORS middleware (from settings), 
   register exception handlers, include v1 router, add Mangum handler for Lambda 
   (conditional on ENVIRONMENT != "local").
7. Verify it starts: uv run uvicorn app.main:app --reload

Commit with message "feat: set up FastAPI app with config, exceptions, and DB session".
```

## BE-2: Database Models + Migrations

```
Read AGENTS.md and docs/lld-backend.md Section 1. Then do BE-2:

1. Implement app/db/base.py -- Base (DeclarativeBase) and TimestampMixin per Section 1.2.
2. Implement app/models/user.py -- User model per Section 1.2.
3. Implement app/models/todo.py -- Todo model with all columns, relationships, and 
   composite indexes per Section 1.2. Also create the todo_labels Table.
4. Implement app/models/section.py -- Section and Subsection models per Section 1.2.
5. Implement app/models/label.py -- Label model per Section 1.2.
6. Implement app/models/reminder.py -- Reminder model per Section 1.2.
7. Update app/models/__init__.py to import all models (so Alembic can detect them).
8. Configure alembic/env.py -- import Base.metadata, import all models, set up async 
   engine from app.core.config, implement run_migrations_online with async.
9. Generate initial migration: uv run alembic revision --autogenerate -m "initial schema"
10. Start DB and apply: docker compose up db -d && uv run alembic upgrade head

Commit with message "feat: add database models and initial migration".
```

## BE-3: Auth Endpoints

```
Read AGENTS.md and docs/lld-backend.md Sections 3.1 and 8. Then do BE-3:

1. Implement app/core/security.py -- create_access_token, verify_token, hash_password, 
   verify_password per Section 8.
2. Implement app/core/dependencies.py -- get_current_user dependency that extracts JWT 
   from Authorization header, verifies it, and returns the User.
3. Create app/schemas/auth.py -- AuthSetup, AuthLogin, AuthToken per Section 2.5.
4. Create app/services/auth_service.py -- AuthService with setup() and login() methods 
   per Section 4.4.
5. Create app/api/v1/routes/auth.py -- POST /auth/setup (201, 409) and POST /auth/login 
   (200, 401) per Section 3.1.
6. Register auth router in app/api/v1/__init__.py.
7. Test manually: start the server, call /api/v1/auth/setup with curl or the Swagger UI 
   at /docs, then call /api/v1/auth/login.

Commit with message "feat: add JWT auth with setup and login endpoints".
```

## BE-4: Todo CRUD API

```
Read AGENTS.md and docs/lld-backend.md Sections 2.2, 3.2, and 4.1. Then do BE-4:

1. Create app/schemas/todo.py -- TodoBase, TodoCreate, TodoUpdate, TodoSchedule, 
   TodoResponse, ReminderCreate, ReminderResponse per Section 2.2.
2. Create app/services/todo_service.py -- TodoService with list_todos (filtering, 
   sorting, pagination), get_todo, create_todo (with label attachment and reminder 
   creation), update_todo (with label re-sync), delete_todo, toggle_complete, 
   schedule_todo per Section 4.1. Use selectinload for labels and reminders.
3. Create app/api/v1/routes/todos.py -- All 7 endpoints per Section 3.2:
   GET /todos (with query params), POST /todos, GET /todos/{id}, PUT /todos/{id}, 
   DELETE /todos/{id}, PATCH /todos/{id}/complete, PATCH /todos/{id}/schedule.
   All protected with Depends(get_current_user).
4. Register todos router in app/api/v1/__init__.py.
5. Test via Swagger UI: create a todo, list todos, update, complete, schedule, delete.

Commit with message "feat: add todo CRUD API with filtering and scheduling".
```

## BE-5: Sections, Subsections, Labels API

```
Read AGENTS.md and docs/lld-backend.md Sections 2.3, 2.4, 3.3, 3.4, 4.2, and 4.3. 
Then do BE-5:

1. Create app/schemas/section.py -- SectionCreate, SubsectionCreate, SubsectionResponse, 
   SectionResponse per Section 2.3.
2. Create app/schemas/label.py -- LabelCreate, LabelResponse per Section 2.4.
3. Create app/services/section_service.py -- SectionService per Section 4.2. Handle 
   cascade rules: deleting a section sets todos.section_id=NULL, deleting a subsection 
   sets todos.subsection_id=NULL.
4. Create app/services/label_service.py -- LabelService per Section 4.3.
5. Create app/api/v1/routes/sections.py -- All 7 endpoints per Section 3.3.
6. Create app/api/v1/routes/labels.py -- All 4 endpoints per Section 3.4.
7. Register both routers in app/api/v1/__init__.py.
8. Test via Swagger UI.

Commit with message "feat: add sections, subsections, and labels CRUD API".
```

## BE-6: Tests

```
Read AGENTS.md and docs/lld-backend.md. Then do BE-6:

1. Implement tests/conftest.py:
   - Create a test PostgreSQL database (or use SQLite async for simplicity)
   - Override get_db dependency with test session
   - Create async test client fixture using httpx.AsyncClient
   - Create fixtures: test_user (calls /auth/setup), auth_headers (JWT token)
   - Create sample data fixtures (sections, labels, todos)

2. Create tests/test_auth.py:
   - Test setup creates user and returns token
   - Test setup fails with 409 if user exists
   - Test login with correct credentials
   - Test login with wrong password returns 401

3. Create tests/test_todos.py:
   - Test create todo (all fields, minimal fields)
   - Test list todos (pagination, filtering by section/priority, sorting)
   - Test get single todo
   - Test update todo (partial update, label re-sync)
   - Test delete todo
   - Test toggle complete / un-complete
   - Test schedule todo (drag-and-drop simulation)

4. Create tests/test_sections.py:
   - Test CRUD for sections and subsections
   - Test cascade: deleting section nullifies todos' section_id

5. Create tests/test_labels.py:
   - Test CRUD for labels
   - Test cascade: deleting label removes from todo_labels

6. Run all tests: uv run pytest -v

Commit with message "test: add comprehensive API tests for all endpoints".
```

---

## INFRA-1: Docker Compose + AWS CDK

```
Read AGENTS.md and docs/lld-backend.md. Then do INFRA-1:

1. Verify and refine docker-compose.yml:
   - Ensure db service healthcheck works
   - Ensure backend service starts correctly after db is healthy
   - Add an init container or entrypoint script that runs alembic upgrade head on startup
   - Test: docker compose up backend db -- verify API is accessible at localhost:8000/docs

2. Create infra/ directory with AWS CDK stack (Python):
   - infra/app.py -- CDK app entry point
   - infra/stacks/api_stack.py -- Lambda function (FastAPI + Mangum), API Gateway v2 (HTTP API)
   - infra/stacks/database_stack.py -- Aurora Serverless v2 (PostgreSQL), VPC, security groups
   - infra/stacks/frontend_stack.py -- S3 bucket + CloudFront distribution for FE static assets
   - infra/stacks/shared_stack.py -- Secrets Manager (JWT_SECRET, DB credentials)
   - infra/requirements.txt -- aws-cdk-lib, constructs

3. Create infra/README.md with deployment instructions:
   - Prerequisites (AWS CLI, CDK CLI)
   - cdk bootstrap, cdk synth, cdk deploy
   - Environment variables and secrets setup

4. Update Makefile with deploy targets:
   - make deploy-staging
   - make deploy-prod

Commit with message "feat: add Docker Compose refinements and AWS CDK infrastructure".
```

## INFRA-2: CI/CD with GitHub Actions

```
Read AGENTS.md. Then do INFRA-2:

1. Create .github/workflows/ci.yml for the backend:
   - Trigger: push to main, pull requests
   - Jobs:
     a. lint: Run ruff check and ruff format --check
     b. typecheck: Run mypy app/
     c. test: Start PostgreSQL service container, run alembic upgrade head, run pytest
   - Use Python 3.13, uv for dependency install

2. Create .github/workflows/deploy.yml for the backend:
   - Trigger: push to main (after CI passes), or manual dispatch
   - Steps: install CDK, cdk synth, cdk deploy --require-approval never
   - Use OIDC role for AWS authentication (no long-lived keys)
   - Environment: staging (auto), production (manual approval)

3. Note: The FE repo CI/CD will be created separately when working in that repo.
   For reference, FE CI would be: lint + typecheck + build + deploy to S3/CloudFront.

Commit with message "ci: add GitHub Actions for linting, testing, and deployment".
```

---

## FE-API-SWAP: Integration (After Both FE and BE are Complete)

```
Read AGENTS.md and docs/lld-frontend.md Section 6. Then do FE-API-SWAP:

1. Create src/data/apiProvider.ts with the same interface as dataProvider but backed 
   by axios calls to the real backend API.
2. Create src/api/client.ts -- axios instance with baseURL from VITE_API_URL, 
   request interceptor for JWT token, response interceptor for 401 redirect.
3. Create src/api/todos.ts, src/api/sections.ts, src/api/labels.ts, src/api/auth.ts 
   with endpoint functions.
4. Swap the export in src/data/provider.ts to use apiProvider.
5. Update Zustand stores to implement optimistic update pattern:
   snapshot -> set -> try API -> catch rollback + toast.error
6. Update LoginPage to call real /api/v1/auth/login and store JWT in localStorage.
7. Test full flow: login -> create todo -> drag to calendar -> verify in DB.

Commit with message "feat: integrate frontend with real backend API".
```
