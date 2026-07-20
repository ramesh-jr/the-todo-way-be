# AI / human handoff — The Todo Way (Life Command Center)

> **Purpose**: Give any new AI session (or human) full product + technical context so work can continue without rediscovering decisions.  
> **Last updated**: 2026-07-20  
> **Canonical copies**: keep in sync in both repos — `the-todo-way-be/docs/ai-context.md` and `the-todo-way-fe/docs/ai-context.md`.  
> **Related**: `docs/plans/v3-life-command-center.md`, `docs/ops-pending.md` (BE), `docs/data-trust.md` (BE), LLD docs, `AGENTS.md`.

---

## 1. What this product is

**The Todo Way** is a personal **Life Command Center**, not a Todoist clone.

Guiding purpose:

> Know what matters, know what is slipping, and make conscious choices instead of reacting randomly.

**Loop**: Capture → Clarify → Engage → Review  

**Hierarchy**: Domains → Priorities → Routines → Next actions  

**Surfaces (FE)**: Today, Inbox, Calendar, Domains, Review, Settings (+ Login / Onboarding).  

**Platform**: Web + installable PWA. Single-user. External calendars (Google / Outlook) are satellites, not the center.

---

## 2. Repos & stack

| Repo | Path (typical) | Stack |
|------|----------------|-------|
| Frontend | `the-todo-way-fe` | React 19, TS, Vite, Tailwind 4, shadcn, FullCalendar, Zustand, React Router 7 |
| Backend | `the-todo-way-be` | Python 3.13, FastAPI, SQLAlchemy async, Alembic, PostgreSQL, JWT + bcrypt, uv |

**Architecture rule (BE)**: Routes (thin) → Services (logic) → Models. Routes never import SQLAlchemy; services never return HTTP responses.

**Data layer (FE)**: `src/data/provider.ts` — `staticProvider` when `VITE_API_URL` unset; `apiProvider` when set. Stores call the provider only.

**Branches**: work has been on `new-approach` (v3 restructure). Confirm with `git branch` before assuming.

---

## 3. Decision history (binding)

Decisions made with the user; treat as product law unless explicitly revisited.

### Foundation

| Decision | Choice | Why |
|----------|--------|-----|
| Path | **Restructure** (Path 2), not evolve-in-place or scrap | Keep stack (React/FullCalendar/shadcn/FastAPI); redesign model & flows |
| Users | **Single-user** | Personal command center; no in-app family multi-user |
| Family calendars | Via **external sync only** | Shared family calendars stay in Google/Outlook |
| Platform | Web + **PWA** | Installable, offline-capable UI |
| Integrations v1 | **Google + Outlook calendar** (read sync designed; write-back later) | Notes/health satellites deferred |
| Schema cutover | **Fresh Alembic migration** `a1b2c3d4e5f6` (no v2 data migration) | Pre-production; old todo schema abandoned |

### Mental models & anti-overwhelm

| Decision | Detail |
|----------|--------|
| Conscious attention | Dashboard leads with focus + wins, not failure |
| Goodhart guard | Family / relationships = **reflection-only** (no checkboxes, counts, or “slipping”) |
| Standards | `countable` (sparse) vs `reflection` (1–5 + note, trend) |
| Seasons | Domain `active` / `maintenance` / `paused` (paused silences nudges; logged) |
| Grace | Missed routines **skip** (never backfill guilt); someday decays; inbox shows age; **no streaks** |
| Energy + context | Filter “what fits now”; tasks (`kind=task`) vs events (`kind=event`) distinct |
| Nudges | Calm, dismissible, rate-limited; never nag |
| Review | Ritual + defer-with-comment allowed |
| Data trust | Export, backup, recovery early — data is never a hostage |

### Local vs production infrastructure

| Env | Database | Notes |
|-----|----------|-------|
| **Local** | **Homebrew Postgres** on laptop | User has **no Docker** access; do not require Docker for local docs/commands |
| **Production** | **Neon or Supabase** (managed Postgres) | Same app; only `DATABASE_URL` (+ secrets) change |

Other local facts discovered in setup:

- Postgres already listens on `5432`; start via `brew services start postgresql@14` (not bare `postgres`).
- If Alembic says `Can't locate revision identified by 'd2f0b0d4a1c7'`, the DB has a **v2 stamp** — drop/recreate DB or wipe `public` schema, then `make migrate` (only revision on v3 is `a1b2c3d4e5f6`).
- FE `demo` token from offline mode caused **401** against live API — FE now rejects `demo` when `VITE_API_URL` is set and redirects on 401.

### Capture / NL behavior

| Behavior | Detail |
|----------|--------|
| Plain capture | `POST /items/capture` → `status=inbox` |
| NL with day (“tomorrow”, weekday, time) | FE `parseQuickAdd` → `createItem` with `status=scheduled` + `scheduled_at` → **skips Inbox** |
| Today | “On the calendar today” = today only; **Coming up** = next 7 days (tasks) so tomorrow captures are visible on home |
| Calendar | Shows all non-done items with `scheduled_at` |

---

## 4. What is already built

### Backend

- Full v3 schema + migration `a1b2c3d4e5f6_life_command_center_schema.py`
- Auth: setup, login, recovery (hashed codes); local returns `dev_code`; `EmailService` (console or SMTP)
- Items: capture, clarify, schedule, complete, CRUD, filters
- Domains, standards, reflections, seasons, priorities, routines (RRULE + grace)
- Reviews, nudges, export JSON/MD, on-demand backup
- Calendar OAuth + sync scaffolding (Google/Outlook clients; needs real credentials)
- Web Push subscribe + VAPID; `scripts/deliver_reminders.py` (`make reminders`)
- `scripts/backup_all.py`, `scripts/import_backup.py`
- Smoke tests in `tests/test_smoke.py` (11 tests; needs `aiosqlite` for in-memory)

### Frontend

- Types + stores: `itemStore`, `domainStore`, `reviewStore`, `uiStore`
- Surfaces: Today, Inbox, Calendar, Domains, Review, Settings, Login, Onboarding
- Capture bar + NL quick-add; clarify dialog; nudges; PWA (`public/sw.js`, `src/lib/pwa.ts`)
- Live API when `VITE_API_URL` set

### Docs / ops scaffolding

- `docs/ops-pending.md` (BE) — human credential / deploy checklist  
- `docs/data-trust.md` (BE)  
- Updated READMEs / AGENTS.md for v3  

---

## 5. What you can test now (local full stack)

**Prerequisites** (already done if app is up):

- BE: Postgres local, `.env` with `DATABASE_URL` + `JWT_SECRET`, `make migrate`, `make dev` → `:8000`
- FE: `.env` with `VITE_API_URL=http://localhost:8000`, `npm run dev` → `:5173`
- Account created via Login → “First time? Set up your account”

### A. Auth & session

- [ ] Setup creates account and seeds default domains  
- [ ] Logout / clear `localStorage.ttw_token` → redirected to login  
- [ ] Login with same credentials works  
- [ ] Recovery request in local: response includes `data.dev_code` or code in BE logs; reset password works  
- [ ] Old `"demo"` token does not grant API access  

### B. Capture → Clarify → Engage

- [ ] Plain capture (`Buy milk`) → appears in **Inbox** with age  
- [ ] Clarify: domain, energy, context, schedule → leaves inbox; shows on Today/Calendar as appropriate  
- [ ] Complete from Today / card  
- [ ] NL: `gym tomorrow 7am ~30m @out` → **skips Inbox**, on **Calendar** + Today **Coming up**; capture hint says skips Inbox  
- [ ] NL today: `call mom today` → Today “On the calendar today”  
- [ ] Someday / mark done / delete paths from clarify or detail  

### C. Today home

- [ ] Week’s focus shows active priorities (empty state OK if none)  
- [ ] Energy/context filter affects “What fits right now” (`active` items)  
- [ ] Agenda today vs Coming up behave as above  
- [ ] Nudge banner calm / dismissible (if any nudges fire)  

### D. Domains

- [ ] Seeded domains visible; Family is reflection-only (cannot add countable “slipping” standards)  
- [ ] Change season (active → maintenance → paused); paused silences related prompts  
- [ ] Add reflection standard + rating + note; see trend if wired  
- [ ] Add countable standard on a non-family domain sparingly  

### E. Priorities & routines

- [ ] Create weekly priorities; they show under Today focus  
- [ ] Create routine with RRULE; generate forward only (no pile of overdue)  
- [ ] Complete / drop priority  

### F. Calendar

- [ ] Drag/drop/resize schedule (if wired for tasks)  
- [ ] Click item opens detail  
- [ ] Overcommit hint if day overloaded (see `OVERCOMMIT_MINUTES` in FE)  
- [ ] External sync: **blocked until OAuth credentials** (see pending)  

### G. Review

- [ ] Open weekly/monthly review flow  
- [ ] Defer with comment  
- [ ] Inbox age / someday decay surfaces if present  

### H. Data trust

- [ ] Settings → export JSON downloads  
- [ ] Export Markdown readable  
- [ ] `POST /api/v1/data/backup` or Settings backup writes under BE `backups/`  
- [ ] `make backup` / `make import-backup ACCOUNT=… FILE=…` (careful: wipe)  

### I. PWA / push (partial without VAPID)

- [ ] Manifest / install prompt in supporting browser  
- [ ] Push subscribe fails gracefully until `VAPID_*` set  
- [ ] With VAPID: subscribe, create reminder, `make reminders`, notification arrives  

### J. API docs

- [ ] http://localhost:8000/docs — exercise a few endpoints with Bearer token  

---

## 6. Pending work

### Needs human / credentials (see `docs/ops-pending.md`)

1. Generate secrets: `JWT_SECRET`, `ENCRYPTION_KEY`, VAPID pair  
2. Google Cloud OAuth → redirect `…/api/v1/calendar/callback/google`  
3. Azure / Entra app → redirect `…/api/v1/calendar/callback/outlook`  
4. SMTP for real recovery email (`SMTP_*`, `ENVIRONMENT=production`)  
5. Schedule cron/EventBridge: `make reminders`, `make backup` + durable storage  
6. Production deploy: FE static host + BE + **Neon/Supabase**; HTTPS; production OAuth redirects  
7. Managed DB snapshots / PITR on Neon/Supabase  

### Product / engineering (no secrets required)

| Item | Notes |
|------|------|
| Calendar **write-back** | Google scope today is read (`calendar.events.readonly`); Outlook similar |
| Conflict UX for sync | When external event conflicts with local edits |
| Webhooks vs polling | Sync is on-demand; push notifications optional later |
| Stronger NL parse | Dates, relative phrases, domains |
| Notes / health satellites | Explicitly deferred |
| Dependencies / waiting-on | Deferred |
| Time-zone polish | Especially NL schedule + calendar |
| FE unit / e2e tests | Sparse today |
| CI + optional CDK/IaC | Personal use can wait |
| Family sharing | Out of v1 by decision |

### Known UX / tech pitfalls

- Capture UI used to say “Goes to Inbox” even when NL scheduled — fixed with conditional copy.  
- Today hid tomorrow items — fixed with **Coming up**.  
- Docker-centric docs are outdated for this user’s laptop — prefer Homebrew / Neon instructions.  
- Mobile shell (2026-07-20): bottom tab nav + overlay drawer; desktop keeps push sidebar. Calendar defaults to Day on small screens.  

---

## 7. How to run locally (no Docker)

```bash
# Postgres (Homebrew) — once
brew services start postgresql@14   # version may vary
# createuser / createdb as needed → match DATABASE_URL

# Backend
cd the-todo-way-be
cp .env.example .env   # DATABASE_URL=postgresql+asyncpg://…@localhost:5432/the_todo_way
uv sync
make migrate
make dev

# Frontend
cd the-todo-way-fe
echo 'VITE_API_URL=http://localhost:8000' > .env
npm install
npm run dev
```

Offline UI only: unset `VITE_API_URL` (static seed; no real auth/API).

---

## 8. Suggested next AI sessions (ordered)

1. **Calendar OAuth end-to-end** once user pastes Google (then Outlook) credentials — verify sync into `kind=event` items.  
2. **VAPID + reminder cron** — wire FE subscribe + job reliability.  
3. **SMTP recovery** — production email path.  
4. **Neon/Supabase prod** — env matrix, migrations, FE build with prod `VITE_API_URL`.  
5. **Write-back + conflict UX** for calendars.  
6. **FE test harness** for capture/clarify/Today filters.  
7. Polish NL + time zones.

When starting a session: read this file, then `AGENTS.md`, then the relevant LLD / `ops-pending.md`. Do not re-litigate binding decisions in §3 without asking the user.

---

## 9. Glossary

| Term | Meaning |
|------|---------|
| Capture | Fast title dump; usually Inbox |
| Clarify | Assign domain / energy / schedule / etc. |
| Engage | Today + Calendar — do the work |
| Review | Periodic ritual over domains/priorities |
| Domain | Life area dashboard (not a todo list) |
| Season | Intentional intensity of a domain |
| Goodhart guard | Don’t turn relationships into metrics |
| Satellite | External system (calendar) synced in |
| Grace | Missed ≠ stacked overdue guilt |
