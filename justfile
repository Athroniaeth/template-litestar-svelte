# Task runner for the Litestar + Vite template — run `just` to list recipes.
# Recipes mirror the pre-commit hooks and are the single source the CI calls.
# Install just: `uv tool install rust-just` (or your package manager).

# List available recipes.
default:
    @just --list

# Install backend deps + the frontend node_modules.
install:
    uv sync
    uv run litestar assets install

# Run the app with hot reload (Litestar + Vite together).
dev:
    uv run litestar run --reload

# Static checks, no writes: ruff + pyrefly (Python), svelte-check (frontend).
lint:
    uv run ruff format --check .
    uv run ruff check .
    uv run pyrefly check
    pnpm -C frontend exec svelte-check

# Apply formatting and safe fixes (Python).
format:
    uv run ruff format .
    uv run ruff check --fix .

# Run the test suite with coverage.
test:
    uv run pytest

# Build the production frontend bundle.
build:
    uv run litestar assets build

# Full gate before pushing (what CI runs): lint + tests.
check: lint test
