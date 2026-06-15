"""Shared schema types and literals."""

from typing import Literal

Season = Literal["active", "maintenance", "paused"]
StandardKind = Literal["countable", "reflection"]
Cadence = Literal["daily", "weekly", "monthly"]
ItemStatus = Literal["inbox", "active", "scheduled", "done", "someday"]
ItemKind = Literal["task", "event"]
Energy = Literal["low", "medium", "high"]
Urgency = Literal["low", "normal", "high"]
Source = Literal["manual", "google", "outlook"]
PriorityStatus = Literal["active", "done", "dropped"]
ReviewType = Literal["daily", "weekly"]
DomainSignal = Literal["on_track", "needs_attention", "paused", "none"]
CalendarProvider = Literal["google", "outlook"]
