"""Geo-IP enrichment via ip-api.com's free tier (no account/API key
required). Private/loopback IPs are short-circuited locally since ip-api
can't geolocate them anyway, and every failure mode falls back to an
"unknown" GeoResult instead of raising -- a broken or rate-limited lookup
must never take down event processing.

This makes an external network call per (uncached) IP, which is the
documented trade-off against an offline database like MaxMind GeoLite2:
zero signup friction, at the cost of an external dependency in the
enrichment path. Swapping in an offline database later only means writing
a new class with the same `lookup` signature.
"""

from __future__ import annotations

import ipaddress
import logging
import time
from collections import OrderedDict

import httpx

from app.metrics import geoip_lookup_duration_seconds, geoip_lookup_failures_total
from app.models import GeoResult

logger = logging.getLogger(__name__)

_UNKNOWN = GeoResult()


class _TTLCache:
    """A tiny bounded, TTL-expiring cache. Good enough for de-duplicating
    geo lookups of repeat visitor IPs within a process; not shared across
    replicas, which is an acceptable trade-off for this cache's only job
    (cutting down on outbound calls to a rate-limited free API)."""

    def __init__(self, max_size: int, ttl_seconds: int) -> None:
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._data: OrderedDict[str, tuple[float, GeoResult]] = OrderedDict()

    def get(self, key: str) -> GeoResult | None:
        entry = self._data.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() >= expires_at:
            del self._data[key]
            return None
        self._data.move_to_end(key)
        return value

    def set(self, key: str, value: GeoResult) -> None:
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = (time.monotonic() + self._ttl, value)
        while len(self._data) > self._max_size:
            self._data.popitem(last=False)


def _is_public_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return not (
        addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved or addr.is_multicast
    )


class GeoIPLookup:
    def __init__(
        self,
        client: httpx.AsyncClient,
        timeout_seconds: float,
        cache_size: int,
        cache_ttl_seconds: int,
    ) -> None:
        self._client = client
        self._timeout = timeout_seconds
        self._cache = _TTLCache(max_size=cache_size, ttl_seconds=cache_ttl_seconds)

    async def lookup(self, ip: str) -> GeoResult:
        if not ip or not _is_public_ip(ip):
            return _UNKNOWN

        cached = self._cache.get(ip)
        if cached is not None:
            return cached

        result = await self._fetch(ip)
        self._cache.set(ip, result)
        return result

    async def _fetch(self, ip: str) -> GeoResult:
        start = time.perf_counter()
        try:
            resp = await self._client.get(
                f"http://ip-api.com/json/{ip}",
                params={"fields": "status,country,countryCode,regionName,city,lat,lon"},
                timeout=self._timeout,
            )
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, ValueError) as e:
            logger.warning("geoip_lookup_failed", extra={"ip": ip, "error": str(e)})
            geoip_lookup_failures_total.inc()
            return _UNKNOWN
        finally:
            geoip_lookup_duration_seconds.observe(time.perf_counter() - start)

        if data.get("status") != "success":
            geoip_lookup_failures_total.inc()
            return _UNKNOWN

        return GeoResult(
            country=data.get("country"),
            country_code=data.get("countryCode"),
            region=data.get("regionName"),
            city=data.get("city"),
            lat=data.get("lat"),
            lon=data.get("lon"),
        )
