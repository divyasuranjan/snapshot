"""Aggregated analytics the dashboard renders: clicks over time, top
referrers, device/browser/OS breakdown, and geo distribution."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Query, Request

from app.db import Repository

router = APIRouter(prefix="/api/stats")

MAX_LOOKBACK_HOURS = 24 * 90  # 90 days


def _truncate(dt: datetime, interval: str) -> datetime:
    if interval == "hour":
        return dt.replace(minute=0, second=0, microsecond=0)
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def build_buckets(interval: str, hours: int, now: datetime | None = None) -> list[datetime]:
    """The full list of bucket start times a timeseries response should
    cover, independent of what data exists -- used to zero-fill gaps so the
    dashboard's chart doesn't mistake "no data" for "missing data"."""
    now = now or datetime.now(UTC)
    start = _truncate(now - timedelta(hours=hours), interval)
    end = _truncate(now, interval)
    step = timedelta(hours=1) if interval == "hour" else timedelta(days=1)

    buckets = []
    cur = start
    while cur <= end:
        buckets.append(cur)
        cur += step
    return buckets


def zero_fill(buckets: list[datetime], raw: list[dict]) -> list[dict]:
    counts = {row["bucket"]: row["clicks"] for row in raw}
    return [{"bucket": b.isoformat(), "clicks": counts.get(b, 0)} for b in buckets]


@router.get("/timeseries")
async def timeseries(
    request: Request,
    interval: Literal["hour", "day"] = "hour",
    hours: int = Query(default=24, ge=1, le=MAX_LOOKBACK_HOURS),
):
    repo: Repository = request.app.state.repo
    raw = await repo.timeseries_raw(interval, hours)
    buckets = build_buckets(interval, hours)
    return {"interval": interval, "hours": hours, "series": zero_fill(buckets, raw)}


@router.get("/referrers")
async def referrers(
    request: Request,
    hours: int = Query(default=24, ge=1, le=MAX_LOOKBACK_HOURS),
    limit: int = Query(default=10, ge=1, le=50),
):
    repo: Repository = request.app.state.repo
    rows = await repo.top_referrers(hours, limit)
    return {"hours": hours, "referrers": rows}


@router.get("/devices")
async def devices(
    request: Request,
    hours: int = Query(default=24, ge=1, le=MAX_LOOKBACK_HOURS),
):
    repo: Repository = request.app.state.repo
    breakdown = await repo.device_breakdown(hours)
    return {"hours": hours, **breakdown}


@router.get("/geo")
async def geo(
    request: Request,
    hours: int = Query(default=24, ge=1, le=MAX_LOOKBACK_HOURS),
    city_limit: int = Query(default=15, ge=1, le=100),
):
    repo: Repository = request.app.state.repo
    distribution = await repo.geo_distribution(hours, city_limit)
    return {"hours": hours, **distribution}
