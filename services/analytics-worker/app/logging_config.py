"""Structured JSON logging, matching shortlink-api's log shape so both
services' logs can be queried the same way downstream."""

from __future__ import annotations

import json
import logging
import sys
import time

_RESERVED = frozenset(logging.LogRecord("", 0, "", 0, "", None, None).__dict__.keys())


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "time": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(record.created))
            + f".{int(record.msecs):03d}Z",
            "level": record.levelname,
            "msg": record.getMessage(),
            "logger": record.name,
        }
        # Anything passed via logging's `extra=` kwarg ends up as an
        # ordinary attribute on the record; surface it in the JSON output
        # instead of dropping it, so callers can attach structured fields
        # (e.g. code=, stream_id=) the way slog's key/value pairs work.
        for key, value in record.__dict__.items():
            if key not in _RESERVED:
                payload[key] = value

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    # Quiet noisy third-party loggers down to warnings; our own JSON
    # formatter still applies to anything they do emit.
    for noisy in ("uvicorn.access",):
        logging.getLogger(noisy).setLevel(logging.WARNING)
