FROM python:3.13-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.11.11 /uv /uvx /bin/

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    UV_COMPILE_BYTECODE=1

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-editable --no-install-project

COPY src src
COPY README.md README.md

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-editable

FROM python:3.13-slim

RUN groupadd --system --gid 999 appgroup \
    && useradd --system --uid 999 --gid appgroup --no-create-home --shell /usr/sbin/nologin appuser

COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"

USER appuser

WORKDIR /app

