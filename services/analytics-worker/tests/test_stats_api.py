from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import health, stats
from app.metrics import MetricsMiddleware
from tests.fakes import FakeRepository


class FakeRedis:
    def __init__(self, fail: bool = False):
        self.fail = fail

    async def ping(self):
        if self.fail:
            raise ConnectionError("redis down")
        return True


def make_client(repo: FakeRepository, redis: FakeRedis) -> TestClient:
    app = FastAPI()
    app.add_middleware(MetricsMiddleware)
    app.include_router(health.router)
    app.include_router(stats.router)
    app.state.repo = repo
    app.state.redis = redis
    return TestClient(app)


def test_healthz():
    client = make_client(FakeRepository(), FakeRedis())
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_readyz_all_up():
    client = make_client(FakeRepository(), FakeRedis())
    resp = client.get("/readyz")
    assert resp.status_code == 200


def test_readyz_database_down():
    repo = FakeRepository()
    repo.ping_error = ConnectionError("db down")
    client = make_client(repo, FakeRedis())
    resp = client.get("/readyz")
    assert resp.status_code == 503
    assert "database" in resp.json()


def test_readyz_redis_down():
    client = make_client(FakeRepository(), FakeRedis(fail=True))
    resp = client.get("/readyz")
    assert resp.status_code == 503
    assert "redis" in resp.json()


def test_timeseries_zero_fills_gaps():
    repo = FakeRepository()
    # The endpoint buckets against the real current time, so the fixture
    # bucket has to be "now" truncated to the hour, not an arbitrary fixed
    # date, or it will never fall inside the generated bucket range.
    current_bucket = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    repo.timeseries_response = [{"bucket": current_bucket, "clicks": 7}]
    client = make_client(repo, FakeRedis())

    resp = client.get("/api/stats/timeseries", params={"interval": "hour", "hours": 3})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["series"]) == 4  # 3 hours back through now, inclusive
    clicks = [p["clicks"] for p in body["series"]]
    assert 7 in clicks
    assert clicks.count(0) == 3


def test_build_buckets_and_zero_fill_pure_functions():
    fixed_now = datetime(2024, 1, 1, 12, 30, tzinfo=UTC)
    buckets = stats.build_buckets("hour", 3, now=fixed_now)

    assert buckets == [
        datetime(2024, 1, 1, 9, tzinfo=UTC),
        datetime(2024, 1, 1, 10, tzinfo=UTC),
        datetime(2024, 1, 1, 11, tzinfo=UTC),
        datetime(2024, 1, 1, 12, tzinfo=UTC),
    ]

    raw = [{"bucket": datetime(2024, 1, 1, 11, tzinfo=UTC), "clicks": 5}]
    filled = stats.zero_fill(buckets, raw)
    assert [p["clicks"] for p in filled] == [0, 0, 5, 0]


def test_timeseries_rejects_invalid_interval():
    client = make_client(FakeRepository(), FakeRedis())
    resp = client.get("/api/stats/timeseries", params={"interval": "fortnight"})
    assert resp.status_code == 422


def test_timeseries_rejects_out_of_range_hours():
    client = make_client(FakeRepository(), FakeRedis())
    resp = client.get("/api/stats/timeseries", params={"hours": 999999})
    assert resp.status_code == 422


def test_referrers():
    repo = FakeRepository()
    repo.referrers_response = [{"referrer": "google.com", "clicks": 42}, {"referrer": "Direct", "clicks": 10}]
    client = make_client(repo, FakeRedis())

    resp = client.get("/api/stats/referrers", params={"limit": 1})
    assert resp.status_code == 200
    assert resp.json()["referrers"] == [{"referrer": "google.com", "clicks": 42}]


def test_devices():
    repo = FakeRepository()
    repo.devices_response = {
        "by_device": [{"name": "desktop", "clicks": 5}],
        "by_browser": [{"name": "Chrome", "clicks": 5}],
        "by_os": [{"name": "Windows", "clicks": 5}],
    }
    client = make_client(repo, FakeRedis())

    resp = client.get("/api/stats/devices")
    assert resp.status_code == 200
    body = resp.json()
    assert body["by_device"][0]["name"] == "desktop"


def test_geo():
    repo = FakeRepository()
    repo.geo_response = {
        "by_country": [{"country": "United States", "country_code": "US", "clicks": 3}],
        "top_cities": [{"city": "Austin", "country_code": "US", "lat": 30.27, "lon": -97.74, "clicks": 3}],
    }
    client = make_client(repo, FakeRedis())

    resp = client.get("/api/stats/geo")
    assert resp.status_code == 200
    body = resp.json()
    assert body["by_country"][0]["country"] == "United States"


def test_metrics_middleware_records_request():
    client = make_client(FakeRepository(), FakeRedis())
    client.get("/healthz")
    # No assertion on the global prometheus registry here to avoid
    # cross-test coupling; this just proves the middleware doesn't break
    # normal request handling.
