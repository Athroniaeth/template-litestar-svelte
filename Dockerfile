# Multi-stage build for a Litestar + Vite app served by Granian. The build stage
# needs Python AND Node: `litestar assets build` generates the TS types from the
# handlers before `vite build`, so the bundle depends on the backend.
FROM node:22-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# LITESTAR_APP/PYTHONPATH let the CLI load the app (normally set via .env); the
# managed CPython lands in /python so the runtime stage can copy it.
ENV UV_PYTHON_INSTALL_DIR=/python UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_COMPILE_BYTECODE=1 UV_PYTHON=3.14 \
    LITESTAR_APP=backend.app:app PYTHONPATH=/app VITE_DEV_MODE=false

WORKDIR /app
COPY . .
RUN corepack enable && uv sync --frozen --no-dev \
    && uv run litestar assets install && uv run litestar assets build

# Runtime: no Node or build tools, just the interpreter + venv + served files.
# index.html ships too — SPA mode rewrites its asset refs from the manifest, and
# vite build emits no public/index.html.
FROM debian:bookworm-slim AS runtime

RUN useradd -m -u 10001 app

COPY --from=builder --chown=app:app /python /python
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/backend /app/backend
COPY --from=builder --chown=app:app /app/frontend/public /app/frontend/public
COPY --from=builder --chown=app:app /app/frontend/index.html /app/frontend/index.html

ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH=/app PYTHONUNBUFFERED=1 \
    LITESTAR_APP=backend.app:app VITE_DEV_MODE=false

USER app
WORKDIR /app
EXPOSE 8000

# GranianPlugin backs `litestar run`; bind all interfaces in the container.
CMD ["litestar", "run", "--host", "0.0.0.0", "--port", "8000"]
