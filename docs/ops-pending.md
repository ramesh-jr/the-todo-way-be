# Ops checklist — items that need you (credentials / consoles / deploy)

Code for the Life Command Center is in place. Everything below needs **your** accounts, secrets, or hosting decisions. Do them in order if you are going from zero to a live personal stack.

---

## 0. Local full stack (no external accounts)

Goal: FE talks to BE with Postgres.

1. **Backend** (local Postgres via Homebrew — Docker is optional and not required)
   ```bash
   brew services start postgresql@14   # or your installed version
   # ensure user/db exist; DATABASE_URL matches .env
   cd the-todo-way-be
   cp .env.example .env
   # Set JWT_SECRET to a long random string
   make migrate
   make dev
   ```
2. **Create account** — `POST http://localhost:8000/api/v1/auth/setup`  
   Body: `{ "username": "you", "password": "…", "recovery_email": "you@example.com" }`  
   Or use the FE onboarding/login once wired.
3. **Frontend**
   ```bash
   cd the-todo-way-fe
   cp .env.example .env   # if present
   # Set: VITE_API_URL=http://localhost:8000
   npm install
   npm run dev
   ```
4. Open `http://localhost:5173`, log in, capture → clarify → Today.

Recovery in local: request recovery; check API response `data.dev_code` or backend logs (no SMTP needed).

---

## 1. Secrets you should generate once

Run these on your machine and paste into `.env` (never commit).

| Variable | How to generate |
|----------|-----------------|
| `JWT_SECRET` | `openssl rand -hex 32` |
| `ENCRYPTION_KEY` | `uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` | `npx web-push generate-vapid-keys` |
| `VAPID_SUBJECT` | `mailto:you@yourdomain.com` |

`ENCRYPTION_KEY` is required before connecting Google/Outlook.  
VAPID keys are required before browser push reminders work.

---

## 2. Google Calendar OAuth (two-way sync)

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → create/select a project.
2. **APIs & Services → Enable APIs** → enable **Google Calendar API**.
3. **OAuth consent screen** → External (or Internal if Workspace) → app name “The Todo Way” → add your email as test user while in Testing.
4. **Credentials → Create OAuth client ID** → type **Web application**.
5. **Authorized redirect URIs** (must match backend exactly):
   - Local: `http://localhost:8000/api/v1/calendar/callback/google`
   - Production: `https://api.yourdomain.com/api/v1/calendar/callback/google`
6. Copy Client ID / Secret → `.env`:
   ```
   GOOGLE_CLIENT_ID=…
   GOOGLE_CLIENT_SECRET=…
   ENCRYPTION_KEY=…   # from step 1
   APP_BASE_URL=http://localhost:8000
   FRONTEND_BASE_URL=http://localhost:5173
   ```
7. Restart backend → Settings → Connect Google → complete consent → Sync.
8. **Before production:** move OAuth consent to Production (or keep Testing + your email as test user), and add the production redirect URI.

**Scopes today:** Google Calendar events **read** (`calendar.events.readonly`). Two-way write-back can be added later by widening scope + implementing create/update/delete on the client.

**Webhooks vs polling:** sync runs on demand (`POST /api/v1/calendar/sync`). Optional later: Google push notifications → public HTTPS callback (needs a stable public URL; ngrok for local experiments).

---

## 3. Microsoft Outlook / Graph OAuth

1. [Azure Portal](https://portal.azure.com/) → **Microsoft Entra ID** → **App registrations** → New registration.
2. Name: “The Todo Way”. Supported account types: personal Microsoft + work/school (or as you prefer).
3. **Redirect URI** → Web →  
   `http://localhost:8000/api/v1/calendar/callback/outlook`  
   (production: `https://api.yourdomain.com/api/v1/calendar/callback/outlook`).
4. **Certificates & secrets** → New client secret → copy value once.
5. **API permissions** → Microsoft Graph → delegated: `Calendars.Read` (or `Calendars.ReadWrite` if you later enable write-back), `offline_access`, `User.Read` → Grant admin consent if required.
6. Copy Application (client) ID and secret → `.env`:
   ```
   MS_CLIENT_ID=…
   MS_CLIENT_SECRET=…
   ```
7. Restart backend → Settings → Connect Outlook → consent → Sync.

---

## 4. Web Push reminders (VAPID)

1. Generate keys (step 1) and set `VAPID_*` in backend `.env`.
2. Expose the public key to the FE (already via API push/vapid endpoint if present — confirm in Settings / PWA subscribe flow).
3. Schedule the delivery job every 1–5 minutes:
   ```cron
   */5 * * * * cd /path/to/the-todo-way-be && make reminders
   ```
   Or EventBridge → Lambda/container invoking `scripts/deliver_reminders.py`.
4. In the browser: allow notifications when prompted; create an item with a reminder; wait for the job tick.

Without VAPID, `make reminders` still clears due rows (logs only) so the queue does not grow forever.

---

## 5. Recovery email (SMTP)

Local already logs codes. For real mail:

1. Pick a provider (examples): Amazon SES, Resend, Postmark, or any SMTP relay.
2. Create SMTP credentials and a verified From address.
3. Set in `.env`:
   ```
   ENVIRONMENT=production   # hides data.dev_code
   SMTP_HOST=email-smtp.…amazonaws.com
   SMTP_PORT=587
   SMTP_USER=…
   SMTP_PASSWORD=…
   SMTP_FROM=noreply@yourdomain.com
   SMTP_USE_TLS=true
   ```
4. Restart API → Settings / recovery flow → request code → check inbox.
5. Confirm `POST /api/v1/auth/recovery/reset` works with that code.

---

## 6. Backups & restore

**Already in code**

- On-demand: `POST /api/v1/data/backup` and Settings export.
- Cron-friendly: `make backup` → files under `backups/`.
- JSON restore: `make import-backup ACCOUNT=you FILE=backups/….json`

**You still need**

1. Daily cron (or Lambda) for `make backup`, and copy `backups/` to durable storage (S3).
2. Managed Postgres automated backups + PITR enabled on the host (RDS/Aurora/Neon/etc.).
3. Document your restore runbook:
   - Preferred: restore DB snapshot → point app at restored DB.
   - Fallback: new empty DB → `make migrate` → create user → `import-backup`.
4. After JSON import: **re-connect calendars** (OAuth tokens are not in the export).

---

## 7. Production deploy (your hosting choice)

**Phone-ready path (recommended):** follow the step-by-step runbook  
→ [`docs/deploy-neon-railway-vercel.md`](./deploy-neon-railway-vercel.md)  
(Neon Postgres → Railway API → Vercel FE + PWA install).

Typical shape:

| Piece | Suggestion |
|-------|------------|
| API | Container on ECS/Fargate, Railway, Fly.io, or Lambda+Mangum |
| DB | Managed Postgres (RDS / Neon / Supabase) |
| FE | Static host (S3+CloudFront, Vercel, Netlify, Cloudflare Pages) |
| Secrets | Host secret manager / env vars — not git |
| Jobs | EventBridge or cron for `reminders` + `backup` |

Checklist when going live:

1. Set `ENVIRONMENT=production`, strong `JWT_SECRET`, real `CORS_ORIGINS`, `APP_BASE_URL`, `FRONTEND_BASE_URL`.
2. Run migrations against production DB once.
3. Point FE `VITE_API_URL` at the production API **at build time**.
4. Add production OAuth redirect URIs (Google + Microsoft).
5. Enable HTTPS everywhere (OAuth and Web Push require it outside localhost).
6. Smoke-test: setup/login, capture, clarify, Today, export, recovery, one calendar sync, one push reminder.

CI/CDK: not required for personal use; add when you want automated checks (`make check` on PR) and infra-as-code.

---

## 8. Deferred product (not ops blockers)

Do these when you want the product to grow — no credentials required until you pick a satellite:

- Notes / health integrations  
- Stronger natural-language parse  
- Dependencies / waiting-on  
- Time-zone polish  
- Frontend unit/e2e tests  
- Conflict UX for calendar write-back  
- Family sharing (explicitly out of v1; external shared calendars only)

---

## Quick “am I done?” matrix

| Capability | Code ready | You must do |
|------------|------------|-------------|
| Capture / clarify / Today / Domains / Review | Yes | Local stack (§0) |
| Export / JSON backup / import script | Yes | Schedule + store backups (§6) |
| Password recovery | Yes (console/dev_code) | SMTP (§5) for real email |
| Web Push reminders | Yes | VAPID keys + cron (§1, §4) |
| Google Calendar | Yes | Google Cloud OAuth (§2) |
| Outlook Calendar | Yes | Azure app registration (§3) |
| Production | Scaffold | Hosting + secrets (§7) |
