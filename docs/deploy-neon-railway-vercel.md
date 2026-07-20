# Deploy runbook — Neon → Railway → Vercel (phone-ready)

Goal: a personal HTTPS stack you can open on your phone, install as a PWA, and keep using away from your laptop.

```
Phone / browser
      │
      ▼
 Vercel (FE static)  ──VITE_API_URL──►  Railway (FastAPI)  ──►  Neon (Postgres)
```

Estimated time: **60–90 minutes** the first time (accounts + wiring). Later deploys are minutes.

---

## Before you start

You need:

- GitHub repos pushed for `the-todo-way-be` and `the-todo-way-fe` (branch you want live, e.g. `new-approach` or `main`)
- Accounts: [Neon](https://neon.tech), [Railway](https://railway.app), [Vercel](https://vercel.com)
- A terminal with `uv` (for one-shot migrations against Neon)

Generate secrets once (save in a password manager; never commit):

```bash
# JWT
openssl rand -hex 32

# Optional now; required before Google/Outlook calendar
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Optional now; required for Web Push on phone
npx web-push generate-vapid-keys
```

**Phone note:** Safari/Chrome need **HTTPS** for installable PWA and for push later. Vercel + Railway custom domains (or their `*.vercel.app` / `*.up.railway.app` URLs) already provide that.

---

## 1. Neon (Postgres)

1. Create a project (region near you).
2. Create a database (default `neondb` is fine) or rename to `the_todo_way`.
3. Dashboard → **Connection details** → copy the connection string.
4. Convert the scheme for this app (async SQLAlchemy):

   | Neon gives you | App needs |
   |----------------|-----------|
   | `postgresql://user:pass@ep-….neon.tech/neondb?sslmode=require` | `postgresql+asyncpg://user:pass@ep-….neon.tech/neondb?ssl=require` |

   Rules:

   - Prefix: `postgresql+asyncpg://`
   - Prefer `ssl=require` (asyncpg). If Neon only shows `sslmode=require`, change it to `ssl=require`.
   - URL-encode special characters in the password if any.

5. Enable **automatic backups / PITR** in the Neon project (default on paid; confirm on free tier).

6. Run migrations from your laptop against Neon (once, before or right after first API deploy):

   ```bash
   cd the-todo-way-be
   DATABASE_URL='postgresql+asyncpg://USER:PASS@HOST/DB?ssl=require' \
     uv run alembic upgrade head
   ```

   If this fails, fix `DATABASE_URL` before wiring Railway — the API will not self-heal a missing schema.

---

## 2. Railway (API)

### 2.1 Create the service

1. New project → **Deploy from GitHub** → select `the-todo-way-be`.
2. Prefer **Dockerfile** deploy (repo already has one).
3. After first deploy, open **Settings → Networking → Generate domain**.  
   Example: `https://the-todo-way-be-production.up.railway.app`  
   Call this **`API_URL`** below (no trailing slash).

### 2.2 Start command (important)

The Dockerfile hardcodes port `8000`. Railway injects `$PORT`. Override the start command so health checks work:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

(Settings → Deploy → Custom Start Command, or equivalent.)

### 2.3 Environment variables

Set these on the Railway service (Variables). Use your real values:

| Variable | Value |
|----------|--------|
| `DATABASE_URL` | Neon async URL from §1 |
| `JWT_SECRET` | `openssl rand -hex 32` output |
| `ENVIRONMENT` | `production` |
| `CORS_ORIGINS` | Temporary: `["https://PLACEHOLDER.vercel.app"]` — update in §3 after FE URL exists |
| `APP_BASE_URL` | `https://your-api.up.railway.app` (= `API_URL`) |
| `FRONTEND_BASE_URL` | Temporary placeholder; update after Vercel |
| `JWT_EXPIRY_DAYS` | `30` (optional; nicer for phone sessions) |

Optional (add when you want the feature):

| Variable | When |
|----------|------|
| `ENCRYPTION_KEY` | Before Google/Outlook |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Calendar sync |
| `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` / `VAPID_SUBJECT` | Browser push |
| `SMTP_*` | Real recovery email (without SMTP, recovery codes only appear in Railway logs) |

Redeploy after changing env vars.

### 2.4 Smoke the API

```bash
curl -sS "$API_URL/docs" | head
# Open $API_URL/docs in a browser — Swagger UI should load
```

Create your account **once** (single-user app):

```bash
curl -sS -X POST "$API_URL/api/v1/auth/setup" \
  -H 'Content-Type: application/json' \
  -d '{"username":"you","password":"choose-a-strong-password","recovery_email":"you@example.com"}'
```

Or skip this and use the FE onboarding after §3.

### 2.5 Jobs (reminders / backup) — later

Railway’s filesystem is **ephemeral**: files under `backups/` can disappear on redeploy. For phone v1:

- Rely on **Neon PITR** + Settings → **Export JSON** often.
- Add a Railway cron / second service later for `uv run python scripts/deliver_reminders.py` once VAPID is set.
- For durable JSON backups, copy off-box (S3) or trigger export from the phone weekly.

---

## 3. Vercel (frontend)

### 3.1 SPA rewrite (do this in the FE repo before first deploy)

Create `the-todo-way-fe/vercel.json` so deep links (`/today`, `/inbox`, …) work on refresh:

```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

Commit and push.

### 3.2 Project setup

1. Vercel → **Add New Project** → import `the-todo-way-fe`.
2. Framework preset: **Vite**.
3. Build command: `npm run build` (default).
4. Output directory: `dist`.
5. Environment variable (**Production**):

   | Name | Value |
   |------|--------|
   | `VITE_API_URL` | `https://your-api.up.railway.app` (no trailing slash) |

   Vite bakes this in at **build** time. Changing the API URL later requires a **redeploy** of the FE.

6. Deploy. Note the URL: `https://the-todo-way-fe.vercel.app` → **`FE_URL`**.

### 3.3 Point Railway back at the real FE

Update Railway:

| Variable | Value |
|----------|--------|
| `CORS_ORIGINS` | `["https://the-todo-way-fe.vercel.app"]` |
| `FRONTEND_BASE_URL` | `https://the-todo-way-fe.vercel.app` |

If you add a custom domain later, put **both** origins in the JSON list:

```json
["https://app.yourdomain.com","https://the-todo-way-fe.vercel.app"]
```

Redeploy Railway (and Vercel if you change `VITE_API_URL`).

---

## 4. Phone smoke test (must pass)

On your phone (same Wi‑Fi or cellular — production URLs, not `localhost`):

1. Open `FE_URL` → set up / log in.
2. Capture `Buy milk` → appears in **Inbox**.
3. Clarify + schedule something for today → shows on **Today**.
4. NL: `gym tomorrow 7am` → Calendar / Coming up (skips Inbox).
5. Settings → Export JSON — download works.
6. **Install PWA**: Safari Share → Add to Home Screen (iOS) or Chrome menu → Install / Add to Home screen (Android).
7. Relaunch from home icon; session should still work (JWT in localStorage; expiry per `JWT_EXPIRY_DAYS`).

If login works on desktop but fails on phone: almost always **CORS** (`CORS_ORIGINS` missing the exact Vercel origin, including `https` and no trailing slash) or wrong `VITE_API_URL` baked into an old FE build.

---

## 5. Optional unlocks (after core works on phone)

### Custom domains (nicer to type)

1. Point `api.yourdomain.com` → Railway; `app.yourdomain.com` → Vercel.
2. Update `APP_BASE_URL`, `FRONTEND_BASE_URL`, `CORS_ORIGINS`, and rebuild FE with new `VITE_API_URL`.

### Google Calendar

1. Google Cloud OAuth Web client.
2. Authorized redirect URI (must match exactly):

   `https://your-api.up.railway.app/api/v1/calendar/callback/google`

3. Set `GOOGLE_*` + `ENCRYPTION_KEY` on Railway; set `APP_BASE_URL` / `FRONTEND_BASE_URL` correctly.
4. Settings → Connect Google → Sync.

Details: `docs/ops-pending.md` §2.

### Web Push reminders

1. Set `VAPID_*` on Railway.
2. Subscribe from the installed PWA (HTTPS required).
3. Schedule delivery every few minutes (Railway cron service or external cron hitting a secured job — today the entrypoint is `make reminders` / `scripts/deliver_reminders.py`).

### Recovery email

Set `SMTP_*` on Railway so password recovery works without reading deploy logs. Until then, keep a strong password and use Export often.

---

## 6. Deploy / update loop

| Change | What to do |
|--------|------------|
| Backend code | Push to connected branch → Railway redeploys. Run `alembic upgrade head` against Neon if there are new migrations. |
| Frontend code | Push → Vercel redeploys. |
| API URL change | Update Vercel `VITE_API_URL` → **Redeploy** FE. |
| New FE domain | Update Railway `CORS_ORIGINS` + `FRONTEND_BASE_URL`. |

Local laptop can keep using Homebrew Postgres + `localhost`; production is a separate `DATABASE_URL`. Do not point local `.env` at Neon unless you intend to edit prod data.

---

## 7. Rollback & data trust

| Problem | Action |
|---------|--------|
| Bad FE deploy | Vercel → Deployments → Promote previous |
| Bad API deploy | Railway → rollback previous deployment |
| Bad data | Neon PITR / branch restore (preferred), or Settings export + `make import-backup` on a clean DB |
| Lost OAuth after restore | Re-connect calendars (tokens not in JSON export) |

---

## 8. “Am I phone-ready?” checklist

- [ ] Neon migrated (`alembic upgrade head`)
- [ ] Railway API serves `/docs` over HTTPS; start command uses `$PORT`
- [ ] Vercel FE has `VITE_API_URL` = Railway URL; `vercel.json` SPA rewrite present
- [ ] Railway `CORS_ORIGINS` includes exact FE origin
- [ ] Account created; capture → clarify → Today works on phone
- [ ] PWA installed on home screen
- [ ] Export JSON once and store somewhere safe
- [ ] (Later) Google OAuth prod redirect + VAPID + reminder cron

---

## Troubleshooting

| Symptom | Likely cause |
|---------|----------------|
| FE loads, API calls fail / CORS error | `CORS_ORIGINS` mismatch or FE built without `VITE_API_URL` |
| FE still hits localhost | Old Vercel build; confirm env + redeploy |
| Railway healthcheck fails | Start command not binding `$PORT` |
| `asyncpg` SSL errors | Use `?ssl=require` on Neon URL |
| Alembic revision errors | Prod DB is empty/new — only v3 revision `a1b2c3d4e5f6` should apply; don’t reuse an old v2 database |
| 401 with old “demo” token | Clear site data; demo token is for offline static provider only |
| Push never arrives | Missing VAPID, no cron for `deliver_reminders`, or permissions denied in browser |

Related: `docs/ops-pending.md`, `docs/data-trust.md`, `docs/ai-context.md`.
