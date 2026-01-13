from collections.abc import AsyncIterator, Iterator

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from injection.loaders import load_packages
from injection.testing import load_test_profile


@pytest.fixture(scope="function", autouse=True)
def load_test_impl() -> Iterator[None]:
    from tests import impl

    load_packages(impl)

    with load_test_profile():
        yield


@pytest.fixture(scope="function", autouse=True)
async def test_client() -> AsyncIterator[AsyncClient]:
    from main import app

    async with LifespanManager(app):
        async with AsyncClient(
            base_url="http://testserver",
            transport=ASGITransport(app=app),
        ) as client:
            yield client
