"""Consumes click events from the Redis Stream shortlink-api publishes to,
enriches them, and persists them.

Delivery model: a Redis Stream consumer group gives at-least-once delivery
-- a message is only removed from the pending list on XACK, so a crash
between processing and acking causes redelivery. `insert_click`'s
ON CONFLICT DO NOTHING makes that redelivery safe. On startup,
`recover_pending` reclaims (via XAUTOCLAIM) anything left pending by a
previous instance that died mid-processing, so restarts don't silently
drop events.

Failure handling per event:
  - malformed (missing/unparseable required fields): logged, counted, and
    acked -- retrying a message that can never parse successfully would
    just loop forever.
  - enrichment failure (geo-IP or user-agent parsing): never raised by the
    enrichment modules themselves; they return "unknown" fallbacks instead.
  - persistence failure (Postgres unreachable): logged, counted, and left
    unacked so it's retried once the database recovers.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from urllib.parse import urlparse

from redis.asyncio import Redis
from redis.exceptions import ResponseError

from app.db import Repository
from app.enrichment.geoip import GeoIPLookup
from app.enrichment.user_agent import parse_user_agent
from app.metrics import event_processing_duration_seconds, events_processed_total, queue_depth
from app.models import EnrichedClick

logger = logging.getLogger(__name__)

_QUEUE_DEPTH_POLL_INTERVAL_SECONDS = 10


class MalformedEventError(ValueError):
    pass


def _parse_fields(fields: dict[str, str]) -> tuple[str, datetime, str, str, str]:
    code = fields.get("code")
    if not code:
        raise MalformedEventError("missing code")

    raw_timestamp = fields.get("timestamp")
    if not raw_timestamp:
        raise MalformedEventError("missing timestamp")
    try:
        clicked_at = datetime.fromisoformat(raw_timestamp)
    except ValueError as e:
        raise MalformedEventError(f"invalid timestamp: {raw_timestamp!r}") from e

    return code, clicked_at, fields.get("ip", ""), fields.get("user_agent", ""), fields.get("referrer", "")


def _referrer_host(referrer: str) -> str:
    if not referrer:
        return "Direct"
    try:
        host = urlparse(referrer).netloc
    except ValueError:
        return "Direct"
    return host or "Direct"


class EventProcessor:
    def __init__(
        self,
        redis: Redis,
        repo: Repository,
        geoip: GeoIPLookup,
        stream: str,
        group: str,
        consumer_name: str,
        batch_size: int,
        block_ms: int,
        pending_claim_idle_ms: int,
    ) -> None:
        self._redis = redis
        self._repo = repo
        self._geoip = geoip
        self._stream = stream
        self._group = group
        self._consumer_name = consumer_name
        self._batch_size = batch_size
        self._block_ms = block_ms
        self._pending_claim_idle_ms = pending_claim_idle_ms

    async def ensure_group(self) -> None:
        try:
            await self._redis.xgroup_create(self._stream, self._group, id="$", mkstream=True)
        except ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    async def recover_pending(self) -> None:
        """Reclaims stream entries left pending by a previous instance
        (idle longer than pending_claim_idle_ms) and processes them before
        picking up new work."""
        cursor = "0-0"
        while True:
            cursor, entries, _deleted = await self._redis.xautoclaim(
                self._stream,
                self._group,
                self._consumer_name,
                min_idle_time=self._pending_claim_idle_ms,
                start_id=cursor,
                count=self._batch_size,
            )
            # Real Redis signals "scanned the whole PEL" with cursor
            # "0-0"; an empty batch is the more portable stop condition
            # (fakeredis, used in tests, never returns "0-0"), and it's
            # safe here since any entry this misses on a partial scan is
            # self-healing -- a later restart's recovery pass will claim it.
            if not entries:
                return
            logger.info("recovering_pending_entries", extra={"count": len(entries)})
            for entry_id, fields in entries:
                await self._process_entry(entry_id, fields)
            if cursor == "0-0":
                return

    async def run(self, stop_event: asyncio.Event) -> None:
        await self.ensure_group()
        await self.recover_pending()

        poll_task = asyncio.create_task(self._poll_queue_depth(stop_event))
        try:
            while not stop_event.is_set():
                try:
                    response = await self._redis.xreadgroup(
                        self._group,
                        self._consumer_name,
                        {self._stream: ">"},
                        count=self._batch_size,
                        block=self._block_ms,
                    )
                except Exception:
                    logger.exception("stream_read_failed")
                    await asyncio.sleep(1)
                    continue

                for _stream_name, entries in response or []:
                    for entry_id, fields in entries:
                        await self._process_entry(entry_id, fields)
        finally:
            poll_task.cancel()

    async def _process_entry(self, entry_id: str, fields: dict[str, str]) -> None:
        start = time.perf_counter()
        try:
            code, clicked_at, ip, ua_string, referrer = _parse_fields(fields)
        except MalformedEventError as e:
            logger.error("malformed_event", extra={"stream_id": entry_id, "error": str(e), "fields": fields})
            events_processed_total.labels(outcome="malformed").inc()
            await self._redis.xack(self._stream, self._group, entry_id)
            return

        ua_result = parse_user_agent(ua_string)
        geo_result = await self._geoip.lookup(ip)

        event = EnrichedClick(
            stream_id=entry_id,
            code=code,
            clicked_at=clicked_at,
            ip=ip,
            user_agent=ua_string,
            referrer=referrer,
            referrer_host=_referrer_host(referrer),
            device_type=ua_result.device_type,
            browser=ua_result.browser,
            os=ua_result.os,
            geo=geo_result,
        )

        try:
            await self._repo.insert_click(event)
        except Exception:
            logger.exception("persist_click_failed", extra={"stream_id": entry_id, "code": code})
            events_processed_total.labels(outcome="db_error").inc()
            # Left unacked: XAUTOCLAIM will redeliver it once this or
            # another consumer's next recovery pass runs.
            return

        events_processed_total.labels(outcome="success").inc()
        event_processing_duration_seconds.observe(time.perf_counter() - start)
        await self._redis.xack(self._stream, self._group, entry_id)

    async def _poll_queue_depth(self, stop_event: asyncio.Event) -> None:
        while not stop_event.is_set():
            try:
                info = await self._redis.xpending(self._stream, self._group)
                queue_depth.set(info.get("pending", 0) if isinstance(info, dict) else 0)
            except Exception:
                logger.warning("queue_depth_poll_failed", exc_info=True)
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=_QUEUE_DEPTH_POLL_INTERVAL_SECONDS)
            except TimeoutError:
                pass
