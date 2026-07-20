#!/usr/bin/env python3
"""Write a JSON backup for every user into ``backups/``.

Usage::

    uv run python scripts/backup_all.py

Schedule daily (example cron)::

    0 3 * * * cd /path/to/the-todo-way-be && uv run python scripts/backup_all.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402

from app.db.session import AsyncSessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.export_service import ExportService  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("backup_all")

BACKUP_DIR = ROOT / "backups"


async def main() -> int:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    async with AsyncSessionLocal() as db:
        users = list(await db.scalars(select(User)))
        for user in users:
            data = await ExportService(db).export_json(user.id)
            path = BACKUP_DIR / f"backup-{user.id}-{stamp}.json"
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            logger.info("Wrote %s", path)
    logger.info("Backed up %s user(s)", len(users))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
