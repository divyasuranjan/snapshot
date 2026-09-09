# Local-dev-only image: bakes both services' migrations into the standard
# Postgres image so a fresh `docker compose up` gets a ready schema with no
# separate migration step. Built with the repo root as context so it can
# reach each service's migrations directory as the single source of truth.
#
# This exists instead of a bind-mounted volume because Docker Desktop's
# host-path translation on macOS cannot bind-mount a path containing a
# literal ":" -- which this project's checkout path does. COPY (a build-time
# operation) isn't affected, since it doesn't go through that translation.
FROM postgres:16-alpine

COPY services/shortlink-api/migrations/0001_init_links.up.sql /docker-entrypoint-initdb.d/01_links.sql
COPY services/analytics-worker/migrations/0001_init_click_events.up.sql /docker-entrypoint-initdb.d/02_click_events.sql
