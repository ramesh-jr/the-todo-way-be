"""Data-trust routes: export (JSON + Markdown) and backup."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.response import ApiResponse
from app.services.export_service import ExportService

router = APIRouter()

_BACKUP_DIR = Path("backups")


@router.get("/export")
async def export_json(
    user: CurrentUser, db: DbSession
) -> ApiResponse[dict[str, Any]]:
    """Full JSON export of the user's command center. Data is never a hostage."""
    data = await ExportService(db).export_json(user.id)
    return ApiResponse(data=data)


@router.get("/export.md", response_class=PlainTextResponse)
async def export_markdown(user: CurrentUser, db: DbSession) -> str:
    """Human-readable Markdown export."""
    return await ExportService(db).export_markdown(user.id)


@router.post("/backup")
async def backup(user: CurrentUser, db: DbSession) -> ApiResponse[dict[str, str]]:
    """Write a timestamped server-side snapshot. See docs for the restore path."""
    data = await ExportService(db).export_json(user.id)
    _BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = _BACKUP_DIR / f"backup-{user.id}-{stamp}.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return ApiResponse(data={"path": str(path), "created_at": stamp})
