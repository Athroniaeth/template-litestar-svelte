import pytest
from litestar.status_codes import (
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)
from litestar.testing import AsyncTestClient, RequestFactory

from backend.exceptions import NotFoundError, ProblemDetail, app_error_handler
from backend.security import API_KEY_ENV_VAR, API_KEY_HEADER


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


@pytest.fixture
def api_key(monkeypatch: pytest.MonkeyPatch) -> str:
    """Configure a known API key for the duration of a test."""
    key = "test-api-key"
    monkeypatch.setenv(API_KEY_ENV_VAR, key)
    return key


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
