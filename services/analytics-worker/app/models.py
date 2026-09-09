"""Data shapes shared across the consumer pipeline and the stats API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class GeoResult:
    """Geo-IP lookup result. Every field is None when the IP is private,
    the lookup failed, or timed out -- enrichment degrading gracefully
    rather than raising."""

    country: str | None = None
    country_code: str | None = None
    region: str | None = None
    city: str | None = None
    lat: float | None = None
    lon: float | None = None


@dataclass(frozen=True)
class UAResult:
    """Parsed user-agent. Falls back to "unknown" fields rather than
    raising when the user-agent string is empty or unparseable."""

    device_type: str = "unknown"
    browser: str = "unknown"
    os: str = "unknown"


@dataclass(frozen=True)
class EnrichedClick:
    """A fully enriched click event, ready to persist."""

    stream_id: str
    code: str
    clicked_at: datetime
    ip: str
    user_agent: str
    referrer: str
    referrer_host: str
    device_type: str
    browser: str
    os: str
    geo: GeoResult
