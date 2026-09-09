# shortlink-api

Go service that creates short links and handles redirects. On every redirect
it publishes a click event onto a Redis Stream for `analytics-worker` to
consume; it never blocks a redirect on that publish succeeding.

## Endpoints

| Method | Path          | Purpose                                   |
|--------|---------------|--------------------------------------------|
| POST   | `/api/links`  | Create a short link. Rate limited per IP.  |
| GET    | `/{code}`     | 302 redirect to the stored long URL.       |
| GET    | `/healthz`    | Liveness probe (process is up).            |
| GET    | `/readyz`     | Readiness probe (Postgres + Redis reachable). |
| GET    | `/metrics`    | Prometheus metrics.                        |

`POST /api/links` request/response:

```
curl -X POST http://localhost:8080/api/links \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com/some/page"}'

{"code":"aZ3kLm9","short_url":"http://localhost:8080/aZ3kLm9","long_url":"https://example.com/some/page","created_at":"2026-01-01T00:00:00Z"}
```

## Configuration (environment variables)

| Variable                 | Required | Default                  | Notes |
|---------------------------|----------|---------------------------|-------|
| `DATABASE_URL`             | yes      | —                          | Postgres DSN |
| `REDIS_ADDR`                | no       | `localhost:6379`          | |
| `REDIS_PASSWORD`            | no       | ``                         | |
| `REDIS_DB`                  | no       | `0`                        | |
| `REDIS_STREAM`              | no       | `clicks`                  | Stream name shared with analytics-worker |
| `REDIS_STREAM_MAXLEN`       | no       | `100000`                  | Approximate cap via `XADD ... MAXLEN ~` |
| `PORT`                      | no       | `8080`                     | |
| `BASE_URL`                  | no       | `http://localhost:8080`   | Used to compose `short_url` in responses |
| `RATE_LIMIT_PER_MINUTE`     | no       | `20`                       | Per-IP, applies to `POST /api/links` only |

## Running locally

Requires Postgres and Redis reachable at the configured addresses, and the
schema in [`migrations/0001_init_links.up.sql`](migrations/0001_init_links.up.sql)
applied.

```bash
go run ./cmd/server
```

## Tests

```bash
go test ./...
```

Handler tests use in-memory fakes for the store/queue/limiter interfaces.
The rate limiter and Redis Stream publisher are tested against
[miniredis](https://github.com/alicebob/miniredis) (a real in-memory Redis
implementation), not mocks, so the actual Lua scripts and stream commands
are exercised.
