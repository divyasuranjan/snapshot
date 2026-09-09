"""Runtime configuration, read from environment variables (the only
configuration source in a container/Kubernetes deployment)."""

from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Config:
    port: int
    log_level: str

    database_url: str
    db_pool_min_size: int
    db_pool_max_size: int

    redis_addr: str
    redis_password: str | None
    redis_db: int
    redis_stream: str
    consumer_group: str
    consumer_name: str
    consumer_batch_size: int
    consumer_block_ms: int
    pending_claim_idle_ms: int

    geoip_timeout_seconds: float
    geoip_cache_size: int
    geoip_cache_ttl_seconds: int

    @staticmethod
    def load() -> Config:
        database_url = os.environ.get("DATABASE_URL", "")
        if not database_url:
            raise ConfigError("DATABASE_URL is required")

        return Config(
            port=_env_int("PORT", 8000),
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
            database_url=database_url,
            db_pool_min_size=_env_int("DB_POOL_MIN_SIZE", 1),
            db_pool_max_size=_env_int("DB_POOL_MAX_SIZE", 5),
            redis_addr=os.environ.get("REDIS_ADDR", "localhost:6379"),
            redis_password=os.environ.get("REDIS_PASSWORD") or None,
            redis_db=_env_int("REDIS_DB", 0),
            redis_stream=os.environ.get("REDIS_STREAM", "clicks"),
            consumer_group=os.environ.get("CONSUMER_GROUP", "analytics-worker"),
            consumer_name=os.environ.get("CONSUMER_NAME", "worker-1"),
            consumer_batch_size=_env_int("CONSUMER_BATCH_SIZE", 10),
            consumer_block_ms=_env_int("CONSUMER_BLOCK_MS", 5000),
            pending_claim_idle_ms=_env_int("PENDING_CLAIM_IDLE_MS", 30_000),
            geoip_timeout_seconds=_env_float("GEOIP_TIMEOUT_SECONDS", 2.0),
            geoip_cache_size=_env_int("GEOIP_CACHE_SIZE", 10_000),
            geoip_cache_ttl_seconds=_env_int("GEOIP_CACHE_TTL_SECONDS", 3600),
        )


def _env_int(key: str, default: int) -> int:
    v = os.environ.get(key)
    if not v:
        return default
    try:
        return int(v)
    except ValueError as e:
        raise ConfigError(f"invalid {key}: {v!r}") from e


def _env_float(key: str, default: float) -> float:
    v = os.environ.get(key)
    if not v:
        return default
    try:
        return float(v)
    except ValueError as e:
        raise ConfigError(f"invalid {key}: {v!r}") from e
