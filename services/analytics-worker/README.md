# analytics-worker

Python/FastAPI service with two jobs in one process:

1. **Consumer**: reads click events off the `clicks` Redis Stream (via a
   consumer group), enriches each one with geo-IP and parsed user-agent
   data, and persists it to Postgres.
2. **Stats API**: serves the aggregated queries the dashboard reads —
   clicks over time, top referrers, device/browser/OS breakdown, and geo
   distribution.

## Delivery and failure handling

Redis Stream consumer groups give at-least-once delivery: a message only
leaves the pending list on `XACK`. That shapes how failures are handled:

| Failure                                   | Behavior |
|--------------------------------------------|----------|
| Malformed event (missing/unparseable fields) | Logged, counted, **acked** — it can never succeed, so retrying forever would just loop. |
| Geo-IP lookup fails or times out            | Falls back to an "unknown" geo — never raises, never blocks persistence. |
| User-agent unparseable                       | Falls back to "unknown" device/browser/OS — never raises. |
| Postgres unreachable                         | Logged, counted, **left unacked** — retried automatically once the database recovers. |

On startup the worker runs `XAUTOCLAIM` to reclaim anything a previous
instance left pending (e.g. it crashed between processing and acking), so a
restart doesn't silently drop events. Inserts are idempotent
(`ON CONFLICT (stream_id) DO NOTHING`), which is what makes redelivery safe.

Geo-IP enrichment calls the free [ip-api.com](http://ip-api.com) API (no
account required) rather than an offline database like MaxMind GeoLite2 —
zero signup friction, at the cost of an external dependency in the
enrichment path. Private/loopback IPs are recognized locally and never
looked up. Results are cached in-process (bounded, TTL-based) to cut down
on repeat calls for the same visitor.

## Endpoints

| Method | Path                     | Purpose |
|--------|--------------------------|---------|
| GET    | `/api/stats/timeseries`  | Clicks over time. `interval=hour\|day`, `hours` (lookback), zero-filled. |
| GET    | `/api/stats/referrers`   | Top referrers by host. `hours`, `limit`. |
| GET    | `/api/stats/devices`     | Breakdown by device type, browser, OS. `hours`. |
| GET    | `/api/stats/geo`         | Clicks by country and top cities (with lat/lon). `hours`, `city_limit`. |
| GET    | `/healthz`               | Liveness probe. |
| GET    | `/readyz`                | Readiness probe (Postgres + Redis reachable). |
| GET    | `/metrics`               | Prometheus metrics. |

## Configuration (environment variables)

| Variable                  | Required | Default            |
|----------------------------|----------|---------------------|
| `DATABASE_URL`               | yes      | —                   |
| `REDIS_ADDR`                  | no       | `localhost:6379`   |
| `REDIS_PASSWORD`              | no       | ``                  |
| `REDIS_STREAM`                | no       | `clicks`            |
| `CONSUMER_GROUP`              | no       | `analytics-worker`  |
| `CONSUMER_NAME`                | no       | `worker-1`          |
| `PORT`                          | no       | `8000`              |
| `GEOIP_TIMEOUT_SECONDS`         | no       | `2.0`               |
| `GEOIP_CACHE_SIZE`              | no       | `10000`             |
| `GEOIP_CACHE_TTL_SECONDS`       | no       | `3600`              |

## Running locally

Requires Postgres and Redis, with the schema in
[`migrations/0001_init_click_events.up.sql`](migrations/0001_init_click_events.up.sql)
applied, and `shortlink-api` (or a raw `XADD` to the `clicks` stream)
producing events.

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

The consumer and its Redis Streams usage (`XREADGROUP`, `XACK`,
`XAUTOCLAIM`) are tested against [fakeredis](https://github.com/cunla/fakeredis-py)'s
async client, a real in-memory Redis implementation, not a mock. Geo-IP
tests mock the HTTP layer with [respx](https://github.com/lundberg/respx)
so they don't depend on network access. The stats API is tested with
FastAPI's `TestClient` against an in-memory repository fake.

## Lint

```bash
ruff check .
```

## Seeding sample data

For a populated dashboard before real traffic exists:

```bash
DATABASE_URL=postgres://... PYTHONPATH=. python scripts/seed_demo_data.py
```

Writes ~600 believable click events (weighted referrers/devices/geo,
skewed toward recent/business hours) directly to Postgres — see
[`scripts/seed_demo_data.py`](scripts/seed_demo_data.py). Set the
dashboard's `DEMO_MODE=true` afterward so it's shown as sample data, not
passed off as live traffic.
