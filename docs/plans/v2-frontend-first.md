# The Todo Way - Frontend-First Plan (v2)

> **Version**: v2 (current)
> **Created**: 2026-02-07
> **Status**: Active

## Changes from v1

1. **Frontend-first development** -- Build entire UI with static JSON dummy data before building the backend. Allows rapid UI iteration without API dependencies.
2. **Static JSON data files** -- `src/data/todos.json`, `sections.json`, `labels.json` provide realistic dummy data matching future API response shapes.
3. **Data provider abstraction** -- `src/data/provider.ts` abstracts data source. Stores call provider, never import JSON directly. Single-line swap when backend is ready.
4. **Reordered phases** -- Phase A (bootstrap), B (FE build), C (BE build), D (integration swap), E (infrastructure).
5. **Only FE repo created initially** -- BE repo deferred to Phase C.

## Build Order

### Phase A: Bootstrap (this step)
- Create FE repo with AGENTS.md, .cursor/rules/, docs/, dummy data
- Git init + initial commit

### Phase B: Frontend (FE-1 through FE-10, one conversation each)
- FE-1: Vite + React + Tailwind + shadcn/ui + design system + dummy data
- FE-2: Types, Zustand stores, data provider
- FE-3: MainLayout + Sidebar + TopBar + routing
- FE-4: LoginPage (static)
- FE-5: TodoCard + CreateTodoDialog + TodoDetailPopup
- FE-6: InboxPage with filtering/sorting
- FE-7: CalendarPage with FullCalendar
- FE-8: LandingPage with drag-and-drop
- FE-9: TodosPage with sections accordion
- FE-10: Dark/light theme

### Phase C: Backend (BE-1 through BE-6)
- FastAPI + SQLAlchemy + Alembic + PostgreSQL
- Auth, CRUD APIs, tests

### Phase D: Integration (FE-API-SWAP)
- Replace data provider with real API client
- Add optimistic updates + error handling

### Phase E: Infrastructure
- Docker Compose + AWS CDK + CI/CD

## Context Management Strategy

- Each conversation handles ONE task from the list above
- AGENTS.md + .cursor/rules/ provide persistent context (auto-loaded)
- Git commits checkpoint progress between conversations
- Subagents used for parallelizable subtasks within a conversation
