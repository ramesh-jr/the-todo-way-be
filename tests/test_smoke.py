"""End-to-end smoke tests covering the core loop and the calm-design guardrails."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_setup_seeds_default_domains(auth_client: AsyncClient) -> None:
    resp = await auth_client.get("/api/v1/domains")
    assert resp.status_code == 200
    domains = resp.json()["data"]
    names = {d["name"] for d in domains}
    assert {"Health", "Family", "Career"} <= names
    family = next(d for d in domains if d["name"] == "Family")
    assert family["reflection_only"] is True


async def test_setup_is_single_user(client: AsyncClient) -> None:
    first = await client.post(
        "/api/v1/auth/setup", json={"username": "alice", "password": "secret123"}
    )
    assert first.status_code == 201
    second = await client.post(
        "/api/v1/auth/setup", json={"username": "bob", "password": "secret123"}
    )
    assert second.status_code == 409


async def test_capture_clarify_complete_loop(auth_client: AsyncClient) -> None:
    # Capture -> lands in inbox.
    cap = await auth_client.post(
        "/api/v1/items/capture", json={"title": "Buy groceries"}
    )
    assert cap.status_code == 201
    item = cap.json()["data"]
    assert item["status"] == "inbox"

    # Clarify -> moves out of inbox with energy/context.
    clar = await auth_client.patch(
        f"/api/v1/items/{item['id']}/clarify",
        json={"energy": "low", "context": ["@errand"]},
    )
    assert clar.status_code == 200
    assert clar.json()["data"]["status"] == "active"
    assert clar.json()["data"]["energy"] == "low"

    # Complete.
    done = await auth_client.patch(f"/api/v1/items/{item['id']}/complete")
    assert done.json()["data"]["status"] == "done"


async def test_energy_context_filter(auth_client: AsyncClient) -> None:
    await auth_client.post(
        "/api/v1/items",
        json={"title": "Deep work", "energy": "high", "context": ["@focus"]},
    )
    await auth_client.post(
        "/api/v1/items",
        json={"title": "Quick call", "energy": "low", "context": ["@phone"]},
    )
    resp = await auth_client.get("/api/v1/items", params={"energy": "low"})
    titles = [i["title"] for i in resp.json()["data"]]
    assert "Quick call" in titles
    assert "Deep work" not in titles


async def test_goodhart_guard_blocks_countable_on_family(
    auth_client: AsyncClient,
) -> None:
    domains = (await auth_client.get("/api/v1/domains")).json()["data"]
    family = next(d for d in domains if d["name"] == "Family")
    resp = await auth_client.post(
        f"/api/v1/domains/{family['id']}/standards",
        json={"text": "Date nights 1x/week", "kind": "countable",
              "cadence": "weekly", "target": 1},
    )
    # Relationships are never counted.
    assert resp.status_code == 400


async def test_season_change_is_respected_and_logged(
    auth_client: AsyncClient,
) -> None:
    domains = (await auth_client.get("/api/v1/domains")).json()["data"]
    health = next(d for d in domains if d["name"] == "Health")
    resp = await auth_client.patch(
        f"/api/v1/domains/{health['id']}/season",
        json={"season": "paused", "note": "work crunch this month"},
    )
    assert resp.json()["data"]["season"] == "paused"
    # Dashboard should list it as an intentional (paused) choice, not a failure.
    dash = (await auth_client.get("/api/v1/domains/dashboard")).json()["data"]
    assert health["id"] in dash["paused_domains"]


async def test_dashboard_leads_with_focus_and_wins(
    auth_client: AsyncClient,
) -> None:
    await auth_client.post("/api/v1/priorities", json={"title": "Ship the MVP"})
    dash = (await auth_client.get("/api/v1/domains/dashboard")).json()["data"]
    assert "focus_priorities" in dash
    assert "recent_wins" in dash
    assert len(dash["focus_priorities"]) == 1


async def test_review_status_and_defer(auth_client: AsyncClient) -> None:
    status = (await auth_client.get("/api/v1/review/status")).json()["data"]
    assert status["is_due"] is True  # never reviewed yet
    deferred = await auth_client.post(
        "/api/v1/review/defer",
        json={"type": "weekly", "reason": "traveling - will do Sunday"},
    )
    assert deferred.json()["data"]["deferred_reason"].startswith("traveling")


async def test_routine_generation_has_grace(auth_client: AsyncClient) -> None:
    # Daily routine; generation fills forward, never backfilling missed days.
    await auth_client.post(
        "/api/v1/routines",
        json={"title": "Morning walk", "rrule": "FREQ=DAILY"},
    )
    gen = await auth_client.post("/api/v1/routines/generate")
    data = gen.json()["data"]
    assert data["generated"] >= 1


async def test_export_is_portable(auth_client: AsyncClient) -> None:
    resp = await auth_client.get("/api/v1/data/export")
    data = resp.json()["data"]
    assert data["version"] == "v3"
    assert "domains" in data and "items" in data


async def test_nudges_are_calm(auth_client: AsyncClient) -> None:
    resp = await auth_client.get("/api/v1/nudges")
    data = resp.json()["data"]
    # A brand-new account is due for its first review -> a gentle primary nudge.
    assert data["primary"] is not None
    assert data["primary"]["kind"] == "weekly_review"
