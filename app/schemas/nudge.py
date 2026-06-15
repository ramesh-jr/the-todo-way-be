"""Nudge schemas.

Nudges are calm, dismissible, rate-limited invitations - never guilt or streaks.
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel

NudgeKind = Literal[
    "weekly_review",
    "unclarified_inbox",
    "overcommitment",
    "someday_decay",
]


class Nudge(BaseModel):
    """A single gentle nudge."""

    kind: NudgeKind
    title: str
    message: str
    # Optional payload (e.g. the over-committed date, or count of inbox items).
    count: int | None = None
    on_date: date | None = None


class NudgeList(BaseModel):
    """At most one prominent nudge is surfaced; the rest are secondary."""

    primary: Nudge | None
    others: list[Nudge]
