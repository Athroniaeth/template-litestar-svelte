from litestar import Litestar, Router
from litestar_granian import GranianPlugin
from litestar_vite import TypeGenConfig, ViteConfig, VitePlugin
from litestar_vite.config import PathConfig, RuntimeConfig

from backend import DEV_MODE, FRONTEND_ROOT
from backend.exceptions import AppError, app_error_handler
from backend.routes import ApiController

config = ViteConfig(
    mode="spa",  # or "template", "htmx", "hybrid", "framework", "external"
    dev_mode=DEV_MODE,
    runtime=RuntimeConfig(executor="pnpm"),
    paths=PathConfig(
        root=FRONTEND_ROOT,
        resource_dir=FRONTEND_ROOT / "src",
        bundle_dir=FRONTEND_ROOT / "public",
        static_dir=FRONTEND_ROOT / "static",
    ),
    types=TypeGenConfig(generate_zod=True),
)
plugins = [VitePlugin(config=config), GranianPlugin(static="auto")]

# All Python routes live under /api to avoid collisions with the Svelte SPA (served
# at / by the Vite plugin). Register every controller here, not with a hardcoded prefix.
api_router = Router(path="/api", route_handlers=[ApiController])

app = Litestar(
    plugins=plugins,
    route_handlers=[api_router],
    exception_handlers={AppError: app_error_handler},
)
