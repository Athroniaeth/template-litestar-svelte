from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]
FRONTEND_ROOT = PROJECT_ROOT / "frontend"

# Versioned API contract: exported from the handlers by `litestar assets
# generate-types`, consumed by the frontend without Python. See the README.
OPENAPI_SCHEMA = PROJECT_ROOT / "openapi.json"
