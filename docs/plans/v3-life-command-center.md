# The Todo Way - Life Command Center (v3)

> **Version**: v3 (current)
> **Created**: 2026-06-02
> **Status**: Active
> **Supersedes**: v2 (frontend-first todo app)

This is the shared, cross-repo plan. The canonical copy lives in both repos' `docs/plans/`.
See `docs/lld-backend.md` for the backend low-level design that implements it.

## Why v3

v2 shipped a Todoist-style task app (Inbox / Calendar / Todos). v3 restructures it into a
single calm **life command center**: external tools (Google / Outlook calendars) become
synced satellites, and the app's job becomes helping you *think, plan, prioritize, and
review* - not just store tasks.

Guiding purpose:

> "Know what matters, know what is slipping, and make conscious choices instead of reacting randomly."

## The hierarchy

```
Life domains  (dashboard: notice what is slipping)
   -> Priorities  (what matters this week/period)
      -> Routines  (repeatable behaviors upholding standards)
         -> Next actions  (the concrete things you do)
```

## Core principles (binding)

1. Conscious attention over failure (lead with focus + wins).
2. Goodhart guard - relationships are reflection-only; Family has no slipping-detector.
3. Standards: `countable` (light signal) vs `reflection` (1-5 + note, trend).
4. Seasons: `active` | `maintenance` | `paused` (paused silences prompts; logged).
5. Grace by default - missed routines skip, someday decays, no streaks.
6. Energy & context on items; tasks vs events distinct.
7. Nudges never nag (calm, dismissible, rate-limited, silenced when paused).
8. Personal command center, not a family coordinator.
9. Data trust early - export, backup, account recovery, sensitive-data handling.

## Backend scope

- Models: domain, standard, reflection_entry, priority, routine, item, label, reminder,
  calendar_connection, domain_state_log, review, push_subscription (+ user recovery fields).
- Fresh Alembic migration replacing the v2 todo-centric schema (pre-production, no data
  migration needed).
- Services + v1 routes: auth (setup/login/recovery), capture, items, domains (+ season),
  standards (+ reflection ratings/trend; no auto-measurement for reflection-only domains),
  priorities, routines (RRULE generation, grace = skip not stack), review (+ defer),
  nudges, export, calendar connections (OAuth + sync), push subscriptions.
- Standard `ApiResponse` envelope throughout.

## Phasing

1. Model + backend end-to-end + Capture/Inbox/Today.
2. Domains dashboard + standards + seasons + priorities + routines + Calendar + Review.
3. Nudges + grace + data trust.
4. PWA + web-push.
5. Calendar sync (Google then Outlook).
6. Onboarding + NL capture + polish.
