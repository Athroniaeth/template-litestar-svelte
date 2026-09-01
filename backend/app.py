from dataclasses import dataclass

from litestar import Litestar, get
from litestar_granian import GranianPlugin
from litestar_vite import ViteConfig, VitePlugin, TypeGenConfig
from litestar_vite.config import PathConfig, RuntimeConfig

from backend import DEV_MODE, FRONTEND_ROOT


@dataclass
class Greeting:
    message: str


@get("/api/hello", name="api:hello")
async def hello() -> Greeting:
    return Greeting(message="Hello from Litestar")

config=ViteConfig(
    mode="spa", # or "template", "htmx", "hybrid", "framework", "external"
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
plugins=[VitePlugin(config=config), GranianPlugin(static="auto")]
app = Litestar(plugins=plugins, route_handlers=[hello])