from litestar import Litestar, Router
from litestar.data_extractors import RequestExtractorField, ResponseExtractorField
from litestar.plugins.structlog import (
    LoggingMiddlewareConfig,
    StructlogConfig,
    StructlogPlugin,
)
from litestar_granian import GranianPlugin
from litestar_vite import TypeGenConfig, ViteConfig, VitePlugin
from litestar_vite.config import PathConfig, RuntimeConfig

from backend import FRONTEND_ROOT, OPENAPI_SCHEMA
from backend.exceptions import AppError, app_error_handler
from backend.routes import ApiController

# Le frontend est servi par nginx, pas par Litestar : `enabled=False` rend le plugin
# inerte au runtime (aucun catch-all HTML, aucun fichier statique, aucun lifespan, pas
# de process Vite). Les commandes `litestar assets *` restent disponibles — `on_cli_init`
# n'est pas court-circuité — donc le plugin ne sert plus qu'à générer les types.
# `mode` et `bundle_dir` ne pilotent que ce codegen et le build Vite.
config = ViteConfig(
    enabled=False,
    mode="spa",
    runtime=RuntimeConfig(executor="pnpm"),
    paths=PathConfig(
        root=FRONTEND_ROOT,
        resource_dir=FRONTEND_ROOT / "src",
        bundle_dir=FRONTEND_ROOT / "dist",
    ),
    # openapi.json sort à la racine du dépôt pour être versionné ; le reste de
    # src/generated/ est dérivé et reste ignoré par git.
    types=TypeGenConfig(generate_zod=True, openapi_path=OPENAPI_SCHEMA),
)
# Structured logging: pretty coloured console on a TTY (dev), JSON otherwise (prod),
# so logs ship straight to Loki/Datadog/ELK without re-parsing. Request/response bodies
# are dropped from the logged fields — they bloat logs and can leak secrets (tokens,
# PII); noisy infra routes are excluded too to keep logs signal.
# Annotated with the library's Literals: a bare `list[str]` would let a misspelled
# field through with nothing flagging it before runtime.
exclude = ["/schema", "/favicon.ico"]
response_log_fields: list[ResponseExtractorField] = [
    "status_code",
    "cookies",
    "headers",
]
request_log_fields: list[RequestExtractorField] = [
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

# `static="auto"` n'aurait plus rien à consommer : l'API ne sert aucun fichier.
# Le nombre de workers vient de WEB_CONCURRENCY, lu nativement par la CLI Granian.
plugins = [
    structlog_plugin,
    VitePlugin(config=config),
    GranianPlugin(),
]

# All Python routes live under /api to avoid collisions with the Svelte SPA (served
# at / by the Vite plugin). Register every controller here, not with a hardcoded prefix.
api_router = Router(path="/api", route_handlers=[ApiController])

app = Litestar(
    plugins=plugins,
    route_handlers=[api_router],
    exception_handlers={AppError: app_error_handler},
)
