"""Prometheus metrics for analytics-worker: HTTP surface, event pipeline,
and enrichment."""

from __future__ import annotations

import time

from prometheus_client import Counter, Gauge, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

http_requests_total = Counter(
    "analytics_worker_http_requests_total",
    "Total HTTP requests handled, by route, method and status.",
    ["route", "method", "status"],
)

http_request_duration_seconds = Histogram(
    "analytics_worker_http_request_duration_seconds",
    "HTTP request latency in seconds, by route and method.",
    ["route", "method"],
)

events_processed_total = Counter(
    "analytics_worker_events_processed_total",
    "Click events read from the stream, by outcome.",
    ["outcome"],  # success | malformed | db_error
)

event_processing_duration_seconds = Histogram(
    "analytics_worker_event_processing_duration_seconds",
    "Time to enrich and persist a single click event, in seconds.",
)

queue_depth = Gauge(
    "analytics_worker_click_queue_depth",
    "Number of entries pending for this consumer group in the click-events stream.",
)

geoip_lookup_duration_seconds = Histogram(
    "analytics_worker_geoip_lookup_duration_seconds",
    "Time spent on outbound geo-IP lookups, in seconds.",
)

geoip_lookup_failures_total = Counter(
    "analytics_worker_geoip_lookup_failures_total",
    "Geo-IP lookups that failed or timed out and fell back to unknown.",
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Records request count and latency per route. `route` is the matched
    route pattern (e.g. "/api/stats/timeseries"), not the raw path, to keep
    metric cardinality bounded."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start

        route = request.scope.get("route")
        route_path = route.path if route is not None else request.url.path

        http_request_duration_seconds.labels(route=route_path, method=request.method).observe(duration)
        http_requests_total.labels(
            route=route_path, method=request.method, status=str(response.status_code)
        ).inc()

        return response
