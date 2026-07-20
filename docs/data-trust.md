# Data Trust: Export, Backup, Recovery

The more this app works, the more catastrophic it is to lose — and it holds sensitive data
(health, family reflections, finances). Trust is treated as a feature, built in early.

## Export (always portable)

- `GET /api/v1/data/export` — full JSON export of domains, standards, priorities, routines,
  items, and reflections. The frontend Settings page downloads this as
  `the-todo-way-export.json`.
- `GET /api/v1/data/export.md` — a human-readable Markdown summary.

The user's data is never a hostage: a complete export is one click away at any time.

## Backup (server-side snapshots)

- `POST /api/v1/data/backup` writes a timestamped JSON snapshot to `backups/` on the server
  (`backup-<user_id>-<UTC timestamp>.json`).
- In production, schedule this (cron / Lambda EventBridge rule) daily, and additionally rely
  on managed Postgres automated backups (e.g. Aurora automated snapshots + PITR).

### Restore path

1. Provision a clean database and run migrations: `alembic upgrade head` (or `make migrate`).
2. Restore from the managed Postgres snapshot (preferred — full fidelity), OR
3. Re-import a JSON snapshot:

   ```bash
   # Create the user first (setup), then:
   make import-backup ACCOUNT=yourname FILE=backups/backup-….json
   # or: uv run python scripts/import_backup.py --username yourname path/to/export.json
   ```

   Calendar OAuth tokens are **not** in the export — reconnect Google/Outlook after import.

### Scheduled backups

```bash
make backup   # writes backups/backup-<user_id>-<stamp>.json for every user
```

Wire to cron / EventBridge daily, and copy `backups/` to durable object storage.

## Account recovery

- A `recovery_email` can be set at `POST /api/v1/auth/setup`.
- `POST /api/v1/auth/recovery/request` issues a short-lived, hashed recovery code (TTL via
  `RECOVERY_CODE_TTL_MINUTES`). Delivery uses `EmailService`: SMTP when configured, otherwise
  console log in local. Local also returns `data.dev_code` for testing. The code is never
  stored in plaintext; the endpoint does not reveal whether an account/email exists.
- `POST /api/v1/auth/recovery/reset` resets the password with a valid, unexpired code.
- Configure SMTP via `SMTP_*` env vars (see `.env.example` and `docs/ops-pending.md`).

## Sensitive-data handling

- OAuth tokens for calendar connections are encrypted at rest with Fernet (`ENCRYPTION_KEY`)
  and never logged.
- Recovery codes are hashed, never stored or logged in plaintext.
- Reflection notes and health-related items are treated as sensitive: excluded from any
  analytics/telemetry, and never written to application logs.
