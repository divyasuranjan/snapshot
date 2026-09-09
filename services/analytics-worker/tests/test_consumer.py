import asyncio

import httpx
import pytest
import respx
from fakeredis import FakeAsyncRedis

from app.consumer import EventProcessor, MalformedEventError, _parse_fields, _referrer_host
from app.enrichment.geoip import GeoIPLookup
from tests.fakes import FakeRepository

STREAM = "clicks"
GROUP = "analytics-worker"


def click_event_fields(code="abc123", ip="8.8.8.8", referrer=""):
    return {
        "code": code,
        "timestamp": "2024-01-01T00:00:00+00:00",
        "ip": ip,
        "user_agent": "UA",
        "referrer": referrer,
    }


def make_processor(redis, repo, geoip=None):
    if geoip is None:
        geoip = GeoIPLookup(
            client=httpx.AsyncClient(), timeout_seconds=1.0, cache_size=10, cache_ttl_seconds=60
        )
    return EventProcessor(
        redis=redis,
        repo=repo,
        geoip=geoip,
        stream=STREAM,
        group=GROUP,
        consumer_name="test-consumer",
        batch_size=10,
        block_ms=100,
        pending_claim_idle_ms=0,
    )


def test_parse_fields_missing_code_raises():
    with pytest.raises(MalformedEventError):
        _parse_fields({"timestamp": "2024-01-01T00:00:00Z"})


def test_parse_fields_missing_timestamp_raises():
    with pytest.raises(MalformedEventError):
        _parse_fields({"code": "abc"})


def test_parse_fields_invalid_timestamp_raises():
    with pytest.raises(MalformedEventError):
        _parse_fields({"code": "abc", "timestamp": "not-a-timestamp"})


def test_parse_fields_success():
    code, clicked_at, ip, ua, referrer = _parse_fields(
        click_event_fields(code="abc", ip="1.2.3.4", referrer="https://google.com/x")
    )
    assert code == "abc"
    assert ip == "1.2.3.4"
    assert ua == "UA"
    assert referrer == "https://google.com/x"


@pytest.mark.parametrize(
    "referrer,expected",
    [
        ("", "Direct"),
        ("https://www.google.com/search?q=x", "www.google.com"),
        ("https://news.ycombinator.com/item?id=1", "news.ycombinator.com"),
    ],
)
def test_referrer_host(referrer, expected):
    assert _referrer_host(referrer) == expected


async def test_ensure_group_is_idempotent():
    redis = FakeAsyncRedis(decode_responses=True)
    repo = FakeRepository()
    processor = make_processor(redis, repo)

    await processor.ensure_group()
    await processor.ensure_group()  # must not raise BUSYGROUP


@respx.mock
async def test_process_entry_valid_event_inserts_and_acks():
    respx.get(url__startswith="http://ip-api.com").mock(
        return_value=httpx.Response(200, json={"status": "success", "country": "Testland"})
    )
    redis = FakeAsyncRedis(decode_responses=True)
    repo = FakeRepository()
    processor = make_processor(redis, repo)
    await processor.ensure_group()

    await redis.xadd(STREAM, click_event_fields())
    response = await redis.xreadgroup(GROUP, "test-consumer", {STREAM: ">"}, count=10)
    entry_id, fields = response[0][1][0]

    await processor._process_entry(entry_id, fields)

    assert len(repo.inserted) == 1
    assert repo.inserted[0].code == "abc123"
    assert repo.inserted[0].geo.country == "Testland"

    pending = await redis.xpending(STREAM, GROUP)
    assert pending["pending"] == 0


async def test_process_entry_malformed_event_is_acked_and_not_persisted():
    redis = FakeAsyncRedis(decode_responses=True)
    repo = FakeRepository()
    processor = make_processor(redis, repo)
    await processor.ensure_group()

    await redis.xadd(STREAM, {"garbage": "field"})
    response = await redis.xreadgroup(GROUP, "test-consumer", {STREAM: ">"}, count=10)
    entry_id, fields = response[0][1][0]

    await processor._process_entry(entry_id, fields)

    assert repo.inserted == []
    pending = await redis.xpending(STREAM, GROUP)
    assert pending["pending"] == 0


@respx.mock
async def test_process_entry_db_error_leaves_message_pending():
    respx.get(url__startswith="http://ip-api.com").mock(
        return_value=httpx.Response(200, json={"status": "fail"})
    )
    redis = FakeAsyncRedis(decode_responses=True)
    repo = FakeRepository()
    repo.insert_error = RuntimeError("db unreachable")
    processor = make_processor(redis, repo)
    await processor.ensure_group()

    await redis.xadd(STREAM, click_event_fields(ip="1.2.3.4"))
    response = await redis.xreadgroup(GROUP, "test-consumer", {STREAM: ">"}, count=10)
    entry_id, fields = response[0][1][0]

    await processor._process_entry(entry_id, fields)

    assert repo.inserted == []
    pending = await redis.xpending(STREAM, GROUP)
    assert pending["pending"] == 1


@respx.mock
async def test_recover_pending_reclaims_and_processes_old_entries():
    respx.get(url__startswith="http://ip-api.com").mock(
        return_value=httpx.Response(200, json={"status": "fail"})
    )
    redis = FakeAsyncRedis(decode_responses=True)
    repo = FakeRepository()

    # Simulate a previous instance that read the message but crashed
    # before acking it: it's in the group's pending list, unacked.
    crashed = make_processor(redis, FakeRepository())
    await crashed.ensure_group()
    await redis.xadd(STREAM, click_event_fields(code="orphan", ip="1.2.3.4"))
    await redis.xreadgroup(GROUP, "dead-consumer", {STREAM: ">"}, count=10)

    pending_before = await redis.xpending(STREAM, GROUP)
    assert pending_before["pending"] == 1

    recoverer = make_processor(redis, repo)
    await recoverer.recover_pending()

    assert len(repo.inserted) == 1
    assert repo.inserted[0].code == "orphan"
    pending_after = await redis.xpending(STREAM, GROUP)
    assert pending_after["pending"] == 0


async def test_run_stops_when_stop_event_is_set():
    redis = FakeAsyncRedis(decode_responses=True)
    repo = FakeRepository()
    processor = make_processor(redis, repo)

    stop_event = asyncio.Event()
    stop_event.set()  # already stopped, so run() should return promptly

    await asyncio.wait_for(processor.run(stop_event), timeout=5)
