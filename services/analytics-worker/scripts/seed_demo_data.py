"""Seeds believable sample click data so the dashboard has something to
show before real traffic exists.

Writes directly to Postgres, bypassing Redis and the enrichment pipeline,
since this is backfilling historical data rather than simulating live
events. Each row gets a unique `seed-NNNNN` stream_id, so `insert_click`'s
ON CONFLICT DO NOTHING makes re-running safe -- it just skips rows already
present.

This only writes to click_events (what the dashboard's stats API reads),
not to shortlink-api's `links` table -- the seeded codes below are for
display purposes and won't resolve as real redirects.

Usage (run from the analytics-worker directory, so `app` is importable):
    DATABASE_URL=postgres://... PYTHONPATH=. python scripts/seed_demo_data.py
"""

from __future__ import annotations

import asyncio
import os
import random
from datetime import UTC, datetime, timedelta

from app.db import PostgresRepository
from app.models import EnrichedClick, GeoResult

random.seed(7)

LINKS = [
    ("launch-week", "https://example.com/blog/launch-week-recap"),
    ("pricing", "https://example.com/pricing"),
    ("docs-quickstart", "https://example.com/docs/quickstart"),
    ("changelog", "https://example.com/changelog"),
    ("demo-signup", "https://example.com/signup"),
]

REFERRERS = [
    ("www.google.com", 0.32),
    ("Direct", 0.24),
    ("news.ycombinator.com", 0.12),
    ("twitter.com", 0.11),
    ("github.com", 0.10),
    ("www.reddit.com", 0.06),
    ("www.linkedin.com", 0.05),
]

# device_type, browser, os, weight
DEVICES = [
    ("desktop", "Chrome", "Windows", 0.30),
    ("desktop", "Safari", "Mac OS X", 0.16),
    ("desktop", "Firefox", "Linux", 0.06),
    ("mobile", "Mobile Safari", "iOS", 0.24),
    ("mobile", "Chrome Mobile", "Android", 0.16),
    ("tablet", "Safari", "iOS", 0.08),
]

# country, country_code, region, city, lat, lon, weight
GEO = [
    ("United States", "US", "Virginia", "Ashburn", 39.03, -77.5, 0.28),
    ("United States", "US", "California", "San Francisco", 37.77, -122.42, 0.14),
    ("United Kingdom", "GB", "England", "London", 51.51, -0.13, 0.13),
    ("Germany", "DE", "Berlin", "Berlin", 52.52, 13.4, 0.09),
    ("India", "IN", "Karnataka", "Bangalore", 12.97, 77.59, 0.12),
    ("Australia", "AU", "New South Wales", "Sydney", -33.87, 151.21, 0.08),
    ("Canada", "CA", "Ontario", "Toronto", 43.65, -79.38, 0.08),
    ("Brazil", "BR", "Sao Paulo", "Sao Paulo", -23.55, -46.63, 0.08),
]


def weighted_choice(options: list[tuple]) -> tuple:
    items = [o[:-1] for o in options]
    weights = [o[-1] for o in options]
    return random.choices(items, weights=weights, k=1)[0]


def random_timestamp(days_back: int) -> datetime:
    now = datetime.now(UTC)
    # Skewed toward 0 (recent) via mode=0, so the trend line trails off
    # further back rather than looking uniformly flat.
    day_offset = random.triangular(0, days_back, 0)
    day = now - timedelta(days=day_offset)
    # Diurnal skew: more clicks in the 13:00-23:00 UTC band (mode=18).
    hour = int(random.triangular(0, 24, 18)) % 24
    return day.replace(hour=hour, minute=random.randint(0, 59), second=random.randint(0, 59), microsecond=0)


async def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")

    count = int(os.environ.get("SEED_COUNT", "600"))
    days_back = int(os.environ.get("SEED_DAYS", "30"))

    repo = await PostgresRepository.connect(database_url, min_size=1, max_size=3)
    try:
        for i in range(count):
            code, _ = random.choice(LINKS)
            device_type, browser, os_name = weighted_choice(DEVICES)
            country, country_code, region, city, lat, lon = weighted_choice(GEO)
            (referrer_host,) = weighted_choice(REFERRERS)

            event = EnrichedClick(
                stream_id=f"seed-{i:05d}",
                code=code,
                clicked_at=random_timestamp(days_back),
                ip="0.0.0.0",
                user_agent="seed-script",
                referrer="" if referrer_host == "Direct" else f"https://{referrer_host}/",
                referrer_host=referrer_host,
                device_type=device_type,
                browser=browser,
                os=os_name,
                geo=GeoResult(
                    country=country, country_code=country_code, region=region, city=city, lat=lat, lon=lon
                ),
            )
            await repo.insert_click(event)

        print(f"Seeded {count} click events across {days_back} days for {len(LINKS)} demo links.")
        print("Demo codes:", ", ".join(code for code, _ in LINKS))
    finally:
        await repo.close()


if __name__ == "__main__":
    asyncio.run(main())
