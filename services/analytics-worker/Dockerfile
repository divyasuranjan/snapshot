# Alpine, not debian-slim: debian-slim drags in util-linux/perl/systemd-libs
# the app never uses, which is where most of a Trivy scan's noise on a
# Python base image comes from. Alpine's minimal package set avoids most of
# it. Trade-off: asyncpg/uvloop have no musl wheels on PyPI, so the builder
# stage compiles them from source -- gcc/musl-dev/postgresql-dev stay out of
# the final image since only the compiled /venv is copied forward.
FROM python:3.12-alpine AS builder
WORKDIR /src

RUN apk add --no-cache gcc musl-dev postgresql-dev

RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-alpine
# The base image tag's package index lags behind Alpine's own security
# repo; patched packages (e.g. libuuid) are already available upstream
# even when the base image was built before they landed.
RUN apk update && apk upgrade --no-cache
RUN adduser --disabled-password --uid 10001 appuser
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

WORKDIR /app
COPY app ./app

USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
