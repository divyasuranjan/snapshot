"""Postgres access: persisting enriched click events and serving the
aggregated queries behind the stats API.

Queries return plain dicts rather than asyncpg.Record, so nothing
Postgres-specific leaks past this module -- callers (including tests) don't
need a database to work with the shapes this returns.
"""

from __future__ import annotations

from typing import Any, Protocol

import asyncpg

from app.models import EnrichedClick

VALID_INTERVALS = {"hour", "day"}


class Repository(Protocol):
    async def ping(self) -> None: ...
    async def insert_click(self, event: EnrichedClick) -> None: ...
    async def timeseries_raw(self, interval: str, since_hours: int) -> list[dict[str, Any]]: ...
    async def top_referrers(self, since_hours: int, limit: int) -> list[dict[str, Any]]: ...
    async def device_breakdown(self, since_hours: int) -> dict[str, list[dict[str, Any]]]: ...
    async def geo_distribution(
        self, since_hours: int, city_limit: int
    ) -> dict[str, list[dict[str, Any]]]: ...


class PostgresRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @classmethod
    async def connect(cls, dsn: str, min_size: int, max_size: int) -> PostgresRepository:
        # Pin the session timezone so timestamptz values round-trip as UTC
        # regardless of the server's configured default -- the stats API's
        # bucket zero-filling assumes consistent UTC on both sides.
        pool = await asyncpg.create_pool(
            dsn=dsn, min_size=min_size, max_size=max_size, server_settings={"timezone": "UTC"}
        )
        return cls(pool)

    async def close(self) -> None:
        await self._pool.close()

    async def ping(self) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute("SELECT 1")

    async def insert_click(self, event: EnrichedClick) -> None:
        # ON CONFLICT DO NOTHING makes this idempotent against redelivery:
        # a consumer crash between insert and XACK causes the same stream
        # entry to be reprocessed, and this must not double-count a click.
        await self._pool.execute(
            """
            INSERT INTO click_events (
                stream_id, code, clicked_at, ip, user_agent, referrer, referrer_host,
                device_type, browser, os, country, country_code, region, city, lat, lon
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            ON CONFLICT (stream_id) DO NOTHING
            """,
            event.stream_id,
            event.code,
            event.clicked_at,
            event.ip,
            event.user_agent,
            event.referrer,
            event.referrer_host,
            event.device_type,
            event.browser,
            event.os,
            event.geo.country,
            event.geo.country_code,
            event.geo.region,
            event.geo.city,
            event.geo.lat,
            event.geo.lon,
        )

    async def timeseries_raw(self, interval: str, since_hours: int) -> list[dict[str, Any]]:
        if interval not in VALID_INTERVALS:
            raise ValueError(f"invalid interval: {interval!r}")

        rows = await self._pool.fetch(
            f"""
            SELECT date_trunc('{interval}', clicked_at) AS bucket, count(*) AS clicks
            FROM click_events
            WHERE clicked_at >= now() - ($1 * interval '1 hour')
            GROUP BY bucket
            ORDER BY bucket
            """,
            since_hours,
        )
        return [{"bucket": r["bucket"], "clicks": r["clicks"]} for r in rows]

    async def top_referrers(self, since_hours: int, limit: int) -> list[dict[str, Any]]:
        rows = await self._pool.fetch(
            """
            SELECT referrer_host, count(*) AS clicks
            FROM click_events
            WHERE clicked_at >= now() - ($1 * interval '1 hour')
            GROUP BY referrer_host
            ORDER BY clicks DESC
            LIMIT $2
            """,
            since_hours,
            limit,
        )
        return [{"referrer": r["referrer_host"], "clicks": r["clicks"]} for r in rows]

    async def device_breakdown(self, since_hours: int) -> dict[str, list[dict[str, Any]]]:
        async def grouped(column: str, limit: int) -> list[dict[str, Any]]:
            rows = await self._pool.fetch(
                f"""
                SELECT {column} AS key, count(*) AS clicks
                FROM click_events
                WHERE clicked_at >= now() - ($1 * interval '1 hour')
                GROUP BY {column}
                ORDER BY clicks DESC
                LIMIT $2
                """,
                since_hours,
                limit,
            )
            return [{"name": r["key"], "clicks": r["clicks"]} for r in rows]

        return {
            "by_device": await grouped("device_type", 10),
            "by_browser": await grouped("browser", 10),
            "by_os": await grouped("os", 10),
        }

    async def geo_distribution(self, since_hours: int, city_limit: int) -> dict[str, list[dict[str, Any]]]:
        countries = await self._pool.fetch(
            """
            SELECT country, country_code, count(*) AS clicks
            FROM click_events
            WHERE clicked_at >= now() - ($1 * interval '1 hour') AND country IS NOT NULL
            GROUP BY country, country_code
            ORDER BY clicks DESC
            """,
            since_hours,
        )
        cities = await self._pool.fetch(
            """
            SELECT city, country_code, avg(lat) AS lat, avg(lon) AS lon, count(*) AS clicks
            FROM click_events
            WHERE clicked_at >= now() - ($1 * interval '1 hour') AND city IS NOT NULL
            GROUP BY city, country_code
            ORDER BY clicks DESC
            LIMIT $2
            """,
            since_hours,
            city_limit,
        )
        return {
            "by_country": [
                {"country": r["country"], "country_code": r["country_code"], "clicks": r["clicks"]}
                for r in countries
            ],
            "top_cities": [
                {
                    "city": r["city"],
                    "country_code": r["country_code"],
                    "lat": r["lat"],
                    "lon": r["lon"],
                    "clicks": r["clicks"],
                }
                for r in cities
            ],
        }
