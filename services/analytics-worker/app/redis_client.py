"""Redis client construction, split out so tests can substitute
fakeredis.FakeAsyncRedis without touching call sites."""

from __future__ import annotations

from redis.asyncio import Redis


def build_redis_client(addr: str, password: str | None, db: int) -> Redis:
    host, _, port = addr.partition(":")
    return Redis(
        host=host or "localhost",
        port=int(port) if port else 6379,
        password=password,
        db=db,
        decode_responses=True,
    )
