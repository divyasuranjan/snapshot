"""In-memory Repository fake shared by consumer and stats API tests."""

from __future__ import annotations

from typing import Any

from app.models import EnrichedClick


class FakeRepository:
    def __init__(self) -> None:
        self.inserted: list[EnrichedClick] = []
        self.ping_error: Exception | None = None
        self.insert_error: Exception | None = None

        self.timeseries_response: list[dict[str, Any]] = []
        self.referrers_response: list[dict[str, Any]] = []
        self.devices_response: dict[str, list[dict[str, Any]]] = {
            "by_device": [],
            "by_browser": [],
            "by_os": [],
        }
        self.geo_response: dict[str, list[dict[str, Any]]] = {"by_country": [], "top_cities": []}

    async def ping(self) -> None:
        if self.ping_error:
            raise self.ping_error

    async def insert_click(self, event: EnrichedClick) -> None:
        if self.insert_error:
            raise self.insert_error
        # Mirrors the real ON CONFLICT (stream_id) DO NOTHING behavior, so
        # tests can exercise idempotency the same way against the fake.
        if any(e.stream_id == event.stream_id for e in self.inserted):
            return
        self.inserted.append(event)

    async def timeseries_raw(self, interval: str, since_hours: int) -> list[dict[str, Any]]:
        return self.timeseries_response

    async def top_referrers(self, since_hours: int, limit: int) -> list[dict[str, Any]]:
        return self.referrers_response[:limit]

    async def device_breakdown(self, since_hours: int) -> dict[str, list[dict[str, Any]]]:
        return self.devices_response

    async def geo_distribution(self, since_hours: int, city_limit: int) -> dict[str, list[dict[str, Any]]]:
        return self.geo_response
