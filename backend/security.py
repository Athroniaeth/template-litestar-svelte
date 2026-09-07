import os
import secrets

from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.handlers.base import BaseRouteHandler

API_KEY_HEADER = "X-API-Key"
API_KEY_ENV_VAR = "API_KEY"


def require_api_key(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Reject the request unless it carries the configured API key.

    The key never reaches the browser: nginx injects the header server-side (and the
    Vite dev proxy does the same in development), so the bundle stays free of secrets.
    Note what this proves — the call came through our proxy, or from a client holding
    the key. It says nothing about *which user* is calling.

    Read from the environment on every call rather than at import time, so tests and
    key rotation do not need a restart.

    Raises:
        NotAuthorizedException: If the key is missing, wrong, or not configured.
    """
    expected = os.getenv(API_KEY_ENV_VAR, "")
    provided = connection.headers.get(API_KEY_HEADER, "")

    # Fail closed: an unset API_KEY locks the route instead of opening it, so a
    # misconfigured deployment cannot silently serve the data to anyone.
    # compare_digest keeps the comparison constant-time, out of reach of timing attacks.
    if not expected or not secrets.compare_digest(provided, expected):
        raise NotAuthorizedException(detail="Invalid or missing API key")
