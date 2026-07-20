#!/usr/bin/env python3
"""Deliver due item reminders via Web Push.

Usage (from repo root)::

    uv run python scripts/deliver_reminders.py

Schedule every 1–5 minutes via cron or a Lambda/EventBridge rule::

    */5 * * * * cd /path/to/the-todo-way-be && uv run python scripts/deliver_reminders.py
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

# Allow `python scripts/...` without installing the package as editable.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.session import AsyncSessionLocal  # noqa: E402
from app.services.reminder_service import ReminderService  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("deliver_reminders")


async def main() -> int:
    async with AsyncSessionLocal() as db:
        result = await ReminderService(db).deliver_due()
    logger.info(
        "Reminders: due=%s sent=%s skipped=%s",
        result["due"],
        result["sent"],
        result["skipped"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
