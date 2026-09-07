import pytest
from litestar import Litestar
from litestar.exceptions import ImproperlyConfiguredException
from litestar.openapi.spec import Components
from litestar.status_codes import (
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)
from litestar.testing import AsyncTestClient, RequestFactory

from backend.app import build_openapi_config
from backend.exceptions import NotFoundError, ProblemDetail, app_error_handler
from backend.security import (
    API_KEY_ENV_VAR,
    API_KEY_HEADER,
    ensure_api_key_configured,
)


async def test_health_check(client: AsyncTestClient):
    response = await client.get("/api/health")
    assert response.status_code == HTTP_200_OK
    assert response.json() == {"status": "ok"}


async def test_root_is_not_served_by_the_api(client: AsyncTestClient):
    """The frontend is served by nginx, not Litestar.

    Guards the decoupling: re-enabling the Vite plugin at runtime would mount an
    HTML catch-all on `/` and silently couple the two again.
    """
    response = await client.get("/")
    assert response.status_code == HTTP_404_NOT_FOUND


async def test_hello_accepts_the_configured_key(client: AsyncTestClient, api_key: str):
    response = await client.get("/api/hello", headers={API_KEY_HEADER: api_key})
    assert response.status_code == HTTP_200_OK
    assert response.json() == {"message": "Hello from Litestar"}


async def test_hello_rejects_a_missing_key(client: AsyncTestClient, api_key: str):
    response = await client.get("/api/hello")
    assert response.status_code == HTTP_401_UNAUTHORIZED


async def test_hello_rejects_a_wrong_key(client: AsyncTestClient, api_key: str):
    response = await client.get("/api/hello", headers={API_KEY_HEADER: "wrong-key"})
    assert response.status_code == HTTP_401_UNAUTHORIZED


async def test_hello_denies_everything_when_no_key_is_configured(
    client: AsyncTestClient, monkeypatch: pytest.MonkeyPatch
):
    """Fail closed: a missing API_KEY must lock the route, not open it."""
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    response = await client.get("/api/hello", headers={API_KEY_HEADER: "any-key"})
    assert response.status_code == HTTP_401_UNAUTHORIZED


async def test_health_stays_public(client: AsyncTestClient, api_key: str):
    """The compose healthcheck reaches /api/health directly, without nginx or a key."""
    response = await client.get("/api/health")
    assert response.status_code == HTTP_200_OK


def test_app_error_handler_maps_to_problem_detail():
    response = app_error_handler(RequestFactory().get("/"), NotFoundError())
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.media_type == "application/problem+json"
    assert response.content == ProblemDetail(
        status=HTTP_404_NOT_FOUND, detail="Resource not found", type="NotFoundError"
    )


def test_startup_check_rejects_a_missing_key(monkeypatch: pytest.MonkeyPatch):
    """Fail fast: a deployment without a key must break loudly, not answer 401s."""
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    with pytest.raises(ImproperlyConfiguredException, match=API_KEY_ENV_VAR):
        ensure_api_key_configured()


def test_startup_check_rejects_an_empty_key(monkeypatch: pytest.MonkeyPatch):
    """An empty value is the Coolify case: nginx then drops the header entirely."""
    monkeypatch.setenv(API_KEY_ENV_VAR, "")
    with pytest.raises(ImproperlyConfiguredException, match=API_KEY_ENV_VAR):
        ensure_api_key_configured()


def test_startup_check_passes_with_a_key(api_key: str):
    ensure_api_key_configured()


async def test_docs_are_served_when_enabled(client: AsyncTestClient):
    """The default: handy in development, and what `generate-types` relies on."""
    response = await client.get("/schema/openapi.json")
    assert response.status_code == HTTP_200_OK


async def test_docs_are_absent_when_disabled():
    """No openapi_config means no /schema router at all.

    Guards production: the API has its own public domain on Coolify, so hiding the
    docs in nginx alone would leave them reachable.
    """
    app_without_docs = Litestar(
        route_handlers=[],
        openapi_config=build_openapi_config(docs_enabled=False),
    )
    async with AsyncTestClient(app=app_without_docs) as client:
        for path in ("/schema", "/schema/openapi.json", "/schema/swagger"):
            assert (await client.get(path)).status_code == HTTP_404_NOT_FOUND


def test_build_openapi_config_returns_none_when_disabled():
    assert build_openapi_config(docs_enabled=False) is None


def test_build_openapi_config_declares_the_api_key_scheme():
    config = build_openapi_config(docs_enabled=True)
    assert config is not None
    # `components` may also be a list in Litestar's API, hence the narrowing.
    components = config.components
    assert isinstance(components, Components)
    assert "APIKey" in (components.security_schemes or {})
