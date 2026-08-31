import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
DEV_MODE = os.getenv("VITE_DEV_MODE", "true").lower() in {"1", "true", "yes"}