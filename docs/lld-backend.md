# The Todo Way - Backend Low-Level Design (v3)

> **Version**: v3 | **Updated**: 2026-06-02
> **Scope**: Backend implementation for the Life Command Center. See `docs/plans/v3-life-command-center.md`.

---

## 1. Database schema

Single-user app. Every top-level entity carries `user_id`. All timestamps are timezone-aware
(`DateTime(timezone=True)`). UUID primary keys.

### Tables

| Table | Purpose |
|-------|---------|
| `users` | Account + auth + recovery |
| `domains` | Life domains (dashboard); hold standards + a season state |
| `standards` | What "good enough" looks like (countable or reflection) |
| `reflection_entries` | Periodic 1-5 self-ratings + notes (trend data) |
| `priorities` | What matters this period (default: week) |
| `routines` | Recurring generators (RRULE) that uphold standards |
| `items` | Captures / next actions / external events |
| `labels` | Optional color tags |
| `item_labels` | M2M join |
| `reminders` | Reminder entries |
| `calendar_connections` | Google / Outlook OAuth accounts + sync state |
| `domain_state_logs` | Season change audit trail |
| `reviews` | Review ritual records (completed / deferred) |
| `push_subscriptions` | Web-push endpoints |

### Key columns

`domains`: `name`, `slug`, `color`, `icon`, `sort_order`, `season` (`active`|`maintenance`|`paused`),
`season_note`, `season_changed_at`, `reflection_only` (bool; true => no countable standards,
no slipping signal - used for Family).

`standards`: `domain_id`, `text`, `kind` (`countable`|`reflection`), `cadence`
(`daily`|`weekly`|`monthly`|null), `target` (int|null), `active`, `sort_order`. Guard:
a standard in a `reflection_only` domain must be `kind=reflection`.

`reflection_entries`: `domain_id`, `standard_id` (nullable), `rating` (1-5, nullable),
`note`, `period_start` (date).

`priorities`: `domain_id` (nullable), `title`, `horizon` (`week`), `status`
(`active`|`done`|`dropped`), `period_start` (date), `sort_order`.

`routines`: `domain_id?`, `standard_id?`, `title`, `rrule` (RFC-5545 string),
`default_energy`, `default_context` (JSON list), `default_duration_minutes`, `active`,
`last_generated_date`. Grace: generation only fills the current horizon forward; missed past
occurrences are never backfilled.

`items`: `title`, `notes`, `status` (`inbox`|`active`|`scheduled`|`done`|`someday`), `kind`
(`task`|`event`), `domain_id?`, `priority_id?`, `routine_id?`, `standard_id?` (countable
only), `energy` (`low`|`medium`|`high`|null), `context` (JSON list of tags), `scheduled_at`,
`duration_minutes`, `deadline_at`, `urgency` (`low`|`normal`|`high`), `rrule?`, `source`
(`manual`|`google`|`outlook`), `external_id?`, `external_calendar_id?`, `someday_reviewed_at?`,
`completed_at?`.

`calendar_connections`: `provider`, `account_email`, `access_token` (encrypted),
`refresh_token` (encrypted), `token_expires_at`, `sync_token`, `calendar_id`, `status`,
`last_synced_at`.

`users` recovery: `recovery_email`, `recovery_code_hash`, `recovery_code_expires_at`.

---

## 2. API (v1) - all responses use `ApiResponse`

### Auth (`/api/v1/auth`)
- `POST /setup` - first user (username + password, optional recovery_email)
- `POST /login`
- `POST /recovery/request` - issue recovery code to recovery_email
- `POST /recovery/reset` - reset password with recovery code

### Capture & Items (`/api/v1/items`)
- `POST /capture` - quick capture (title + optional NL parse hints) -> inbox item
- `GET /` - list with filters (`status`, `domain_id`, `priority_id`, `energy`, `context`,
  `kind`, `date_from`, `date_to`, `max_minutes`)
- `POST /`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}`
- `PATCH /{id}/clarify` - assign domain/priority/energy/context/schedule, move out of inbox
- `PATCH /{id}/complete`, `PATCH /{id}/schedule`, `PATCH /{id}/someday`

### Domains (`/api/v1/domains`)
- `GET /` (with standards), `POST /`, `PUT /{id}`, `DELETE /{id}`
- `PATCH /{id}/season` - set active/maintenance/paused (+ note); logged
- `GET /dashboard` - conscious-attention dashboard payload (focus, wins, gentle invitations)

### Standards & reflections (`/api/v1/domains/{id}/standards`, `/api/v1/standards`)
- `POST`, `PUT /{id}`, `DELETE /{id}`
- `POST /{id}/reflections` - add 1-5 rating + note
- `GET /{id}/trend` - reflection trend series

### Priorities (`/api/v1/priorities`)
- `GET /` (current period default), `POST`, `PUT /{id}`, `DELETE /{id}`, `PATCH /{id}/status`

### Routines (`/api/v1/routines`)
- `GET /`, `POST`, `PUT /{id}`, `DELETE /{id}`
- `POST /generate` - materialize due instances into items (grace: skip missed)

### Review (`/api/v1/review`)
- `GET /status` - is a review due? last review, deferral state, gentle re-entry signal
- `POST /complete`, `POST /defer` (reason + until)

### Nudges (`/api/v1/nudges`)
- `GET /` - current calm nudges (weekly-review, unclarified-inbox, overcommitment,
  someday-decay), each dismissible + rate-limited; paused domains excluded.

### Data trust (`/api/v1/data`)
- `GET /export` - full JSON export
- `GET /export.md` - human-readable export
- `POST /backup` - trigger server-side backup (documented restore path)

### Calendar sync (`/api/v1/calendar`)
- `GET /connections`, `POST /connect/{provider}` (OAuth start), `GET /callback/{provider}`,
  `DELETE /connections/{id}`, `POST /sync` (incremental). External events map to
  `items` with `kind=event`, `source=provider`.

### Push (`/api/v1/push`)
- `GET /vapid-public-key`, `POST /subscribe`, `DELETE /subscribe`

---

## 3. Layering (unchanged discipline)

Routes (thin) -> Services (business logic, all queries) -> Models. Routes never import
SQLAlchemy; services never return HTTP responses. Async throughout.

Key services: `AuthService`, `ItemService`, `DomainService`, `StandardService`,
`PriorityService`, `RoutineService` (RRULE via `dateutil.rrule`), `ReviewService`,
`NudgeService` (computes calm nudges + slipping signals, honoring seasons + Goodhart guard),
`ExportService`, `CalendarSyncService` (+ `GoogleCalendarClient`, `OutlookCalendarClient`),
`PushService`.

## 4. Slipping signal (countable only)

`NudgeService.compute_domain_signals` measures completed items / routine instances tagged to
a countable standard against its `target` over the standard's `cadence` window. Output is a
calm tri-state (`on_track` | `needs_attention` | `paused`), never a streak or score.
`reflection_only` domains and `reflection` standards are never measured - they only surface a
"due for a reflection" invitation.

## 5. Security & config

JWT (python-jose, HS256). Passwords + recovery codes hashed with passlib[bcrypt]. New env
vars: `ENCRYPTION_KEY` (Fernet, for OAuth tokens), `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`,
`VAPID_SUBJECT`, `GOOGLE_CLIENT_ID/SECRET`, `MS_CLIENT_ID/SECRET`, `OAUTH_REDIRECT_BASE`.
Sensitive fields (OAuth tokens, recovery code) are encrypted at rest / hashed and never
logged.
