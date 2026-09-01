import pytest
from litestar.status_codes import HTTP_200_OK
from litestar.testing import AsyncTestClient




async def test_health_check(client: AsyncTestClient):
    response = await client.get("/api/health")
    assert response.status_code == HTTP_200_OK
    assert response.json() == {"status": "ok"}
