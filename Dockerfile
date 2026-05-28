# TenderIQ API — production container for Google Cloud Run (asia-south1).
#
# Build context is the REPO ROOT (C:\bid) so we can pull in both /api (the
# FastAPI source + uv project) and /shared (the Citation contract that /api
# imports as `shared.citation`).
#
# Multi-stage build using uv to install deps into a frozen venv, then a small
# runtime image with only the venv and the source. Cloud Run injects PORT;
# uvicorn binds to it. ADC for Vertex is picked up from the Cloud Run runtime
# service account (no key file shipped).

ARG PYTHON_VERSION=3.12-slim-bookworm

# ----- build stage -----
FROM python:${PYTHON_VERSION} AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9.16 /uv /usr/local/bin/uv

WORKDIR /app
COPY api/pyproject.toml api/uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY api/ ./
COPY shared/ /app/shared/
RUN uv sync --frozen --no-dev

# ----- runtime stage -----
FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8080

RUN apt-get update && apt-get install -y --no-install-recommends \
        libjpeg62-turbo libpng16-16 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

RUN groupadd --system app && useradd --system --gid app --home /app app \
    && chown -R app:app /app
USER app

EXPOSE 8080
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 1 --proxy-headers --forwarded-allow-ips='*'
