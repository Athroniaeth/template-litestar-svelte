from litestar import Litestar, Router
from litestar.plugins.structlog import (
    LoggingMiddlewareConfig,
    StructlogConfig,
    StructlogPlugin,
)
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
# Structured logging: pretty coloured console on a TTY (dev), JSON otherwise (prod),
# so logs ship straight to Loki/Datadog/ELK without re-parsing. Request/response bodies
# are dropped from the logged fields — they bloat logs and can leak secrets (tokens,
# PII); noisy infra routes are excluded too to keep logs signal.
exclude = ["/schema", "/static", "/favicon.ico"]
response_log_fields = ["status_code", "cookies", "headers"]
request_log_fields = [
    "path",
    "method",
    "content_type",
    "headers",
    "cookies",
    "query",
    "path_params",
]

middleware_logging_config = LoggingMiddlewareConfig(
    exclude=exclude,
    request_log_fields=request_log_fields,
    response_log_fields=response_log_fields,
)
structlog_config = StructlogConfig(middleware_logging_config=middleware_logging_config)
structlog_plugin = StructlogPlugin(config=structlog_config)

plugins = [
    structlog_plugin,
    VitePlugin(config=config),
    GranianPlugin(static="auto"),
]

# All Python routes live under /api to avoid collisions with the Svelte SPA (served
# at / by the Vite plugin). Register every controller here, not with a hardcoded prefix.
api_router = Router(path="/api", route_handlers=[ApiController])

app = Litestar(
    plugins=plugins,
    route_handlers=[api_router],
    exception_handlers={AppError: app_error_handler},
)
