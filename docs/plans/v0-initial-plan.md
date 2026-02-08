# The Todo Way - Initial Plan (v0)

> **Version**: v0
> **Created**: 2026-02-07
> **Status**: Superseded by v1

## Summary

Initial project plan for a Todoist-like todo app with Inbox, Calendar, and Todos sections.

## Original Decisions

- **Frontend**: React 19 + TypeScript + Vite 6 + Tailwind CSS + shadcn/ui
- **Backend**: Node.js + Fastify + Drizzle ORM + TypeScript
- **Calendar**: Custom-built from scratch using date-fns
- **Drag & Drop**: @dnd-kit/core
- **Database**: PostgreSQL 16
- **Infrastructure**: AWS serverless (Lambda, Aurora Serverless, S3 + CloudFront)
- **Auth**: Simple JWT, single user
- **Deployment**: SST v3 (Serverless Stack)

## Key Requirements

1. Todo creation with: title, description, date/time, priority, reminders, labels, section/subsection, deadline, location, duration
2. Inbox: card list of all incomplete todos, configurable display fields
3. Calendar: Outlook-style with mini month view + time grid, multiple views (day, 3-day, working week, week, month)
4. Landing page: split pane with Inbox (left) and Calendar (right), drag-and-drop from inbox to calendar
5. Todo detail popup: modal for viewing/editing all fields

## What Changed in v1

- Calendar component changed from custom-built to FullCalendar (after feasibility analysis)
- Backend changed from Node.js/Fastify to Python/FastAPI
- Added UI Design System / Branding
- Added Docker Compose for local dev mirroring AWS
- Plan document versioning introduced
