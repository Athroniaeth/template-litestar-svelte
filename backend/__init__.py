from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]
FRONTEND_ROOT = PROJECT_ROOT / "frontend"

# Contrat d'API versionné : exporté depuis les handlers par `litestar assets
# generate-types`, consommé par le frontend sans Python. Voir README.
OPENAPI_SCHEMA = PROJECT_ROOT / "openapi.json"
