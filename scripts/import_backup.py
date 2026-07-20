#!/usr/bin/env python3
"""Restore a v3 JSON export into an existing user account.

Prefer a managed Postgres snapshot restore when available. Use this script when
you only have a JSON file from ``GET /api/v1/data/export`` or ``scripts/backup_all.py``.

Usage::

    uv run python scripts/import_backup.py --username alice backups/backup-....json

By default the user's existing command-center data is wiped first (account kept).
Pass ``--no-wipe`` only for empty accounts.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402

from app.db.session import AsyncSessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.import_service import ImportService  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("import_backup")


async def main() -> int:
    parser = argparse.ArgumentParser(description="Import a v3 JSON backup")
    parser.add_argument("path", type=Path, help="Path to export JSON")
    parser.add_argument(
        "--username", required=True, help="Existing account to import into"
    )
    parser.add_argument(
        "--no-wipe",
        action="store_true",
        help="Do not delete existing data first (dangerous if data already exists)",
    )
    args = parser.parse_args()

    if not args.path.is_file():
        logger.error("File not found: %s", args.path)
        return 1

    payload = json.loads(args.path.read_text(encoding="utf-8"))

    async with AsyncSessionLocal() as db:
        user = await db.scalar(select(User).where(User.username == args.username))
        if user is None:
            logger.error("No user named %r", args.username)
            return 1
        counts = await ImportService(db).import_json(
            user.id, payload, wipe=not args.no_wipe
        )

    logger.info("Import complete for %s: %s", args.username, counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
