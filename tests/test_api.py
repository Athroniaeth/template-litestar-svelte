from litestar.status_codes import HTTP_200_OK, HTTP_404_NOT_FOUND
from litestar.testing import AsyncTestClient, RequestFactory

from backend.exceptions import NotFoundError, ProblemDetail, app_error_handler


async def test_health_check(client: AsyncTestClient):
    response = await client.get("/api/health")
    assert response.status_code == HTTP_200_OK
    assert response.json() == {"status": "ok"}


async def test_hello(client: AsyncTestClient):
    response = await client.get("/api/hello")
    assert response.status_code == HTTP_200_OK
    assert response.json() == {"message": "Hello from Litestar"}


def test_app_error_handler_maps_to_problem_detail():
    response = app_error_handler(RequestFactory().get("/"), NotFoundError())
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.media_type == "application/problem+json"
    assert response.content == ProblemDetail(
        status=HTTP_404_NOT_FOUND, detail="Resource not found", type="NotFoundError"
    )
