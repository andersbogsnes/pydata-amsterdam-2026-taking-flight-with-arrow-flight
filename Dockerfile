FROM python:3.13-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.1 /uv /bin/

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    UV_PYTHON_DOWNLOADS=0 \
    UV_COMPILE_BYTECODE=1

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-workspace

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

FROM python:3.13-slim


COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

CMD ["jupyter", "lab", "--ip", "0.0.0.0", "--port", "8080", "--notebook-dir", "/app/notebooks", \
"--IdentityProvider.token=''", "--ServerApp.password=''", "--no-browser", "--allow-root"]