"""analytics-worker: consumes click events from Redis, enriches and
persists them to Postgres, and serves the aggregated stats API the
dashboard reads from. The consumer runs as a background task alongside the
HTTP server in the same process -- this is a single-container service, not
a bus deserving its own deployment."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from redis.asyncio import Redis

from app.api import health, stats
from app.config import Config
from app.consumer import EventProcessor
from app.db import PostgresRepository
from app.enrichment.geoip import GeoIPLookup
from app.logging_config import configure_logging
from app.metrics import MetricsMiddleware
from app.redis_client import build_redis_client

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = Config.load()
    configure_logging(cfg.log_level)

    repo = await PostgresRepository.connect(cfg.database_url, cfg.db_pool_min_size, cfg.db_pool_max_size)
    redis: Redis = build_redis_client(cfg.redis_addr, cfg.redis_password, cfg.redis_db)
    await redis.ping()

    http_client = httpx.AsyncClient()
    geoip = GeoIPLookup(
        client=http_client,
        timeout_seconds=cfg.geoip_timeout_seconds,
        cache_size=cfg.geoip_cache_size,
        cache_ttl_seconds=cfg.geoip_cache_ttl_seconds,
    )

    processor = EventProcessor(
        redis=redis,
        repo=repo,
        geoip=geoip,
        stream=cfg.redis_stream,
        group=cfg.consumer_group,
        consumer_name=cfg.consumer_name,
        batch_size=cfg.consumer_batch_size,
        block_ms=cfg.consumer_block_ms,
        pending_claim_idle_ms=cfg.pending_claim_idle_ms,
    )

    app.state.repo = repo
    app.state.redis = redis

    stop_event = asyncio.Event()
    consumer_task = asyncio.create_task(processor.run(stop_event))

    logger.info("started", extra={"port": cfg.port, "stream": cfg.redis_stream})
    try:
        yield
    finally:
        stop_event.set()
        consumer_task.cancel()
        try:
            await consumer_task
        except (asyncio.CancelledError, Exception):
            pass
        await http_client.aclose()
        await redis.aclose()
        await repo.close()
        logger.info("shutdown_complete")


def create_app() -> FastAPI:
    app = FastAPI(title="analytics-worker", lifespan=lifespan)

    app.add_middleware(MetricsMiddleware)
    # No auth and no per-tenant data in this project (see README), so an
    # open CORS policy is a deliberate simplification, not an oversight --
    # the dashboard is the only intended caller.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(stats.router)

    @app.get("/metrics")
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
