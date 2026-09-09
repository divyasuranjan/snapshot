from __future__ import annotations

import asyncio

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

router = APIRouter()

_READY_TIMEOUT_SECONDS = 3


@router.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(request: Request) -> Response:
    repo = request.app.state.repo
    redis = request.app.state.redis

    async def check(coro) -> str | None:
        try:
            await asyncio.wait_for(coro, timeout=_READY_TIMEOUT_SECONDS)
            return None
        except Exception as e:
            return str(e)

    db_err, redis_err = await asyncio.gather(check(repo.ping()), check(redis.ping()))

    if db_err or redis_err:
        body = {"status": "not ready"}
        if db_err:
            body["database"] = db_err
        if redis_err:
            body["redis"] = redis_err
        return JSONResponse(body, status_code=503)

    return JSONResponse({"status": "ready"})
