import inspect
from typing import AsyncIterator

import pytest
from litestar import Litestar
from litestar.testing import AsyncTestClient

from backend.app import app


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Auto-apply the `anyio` marker to every async test.

    Avoids having to declare `pytestmark = pytest.mark.anyio` in every test module.
    """
    for item in items:
        if inspect.iscoroutinefunction(getattr(item, "function", None)):
            item.add_marker("anyio")


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Configure anyio to use asyncio, else `pytestmark = pytest.mark.anyio` does not work."""
    return "asyncio"


@pytest.fixture(scope="session")
async def client() -> AsyncIterator[AsyncTestClient[Litestar]]:
    """Fixture for creating an async test client."""
    app.debug = True
    async with AsyncTestClient(app=app) as _client:
        yield _client
