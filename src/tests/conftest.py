# import pytest
# import pytest_asyncio
# from httpx import AsyncClient
#
# from main import app
#
# pytestmark = pytest.mark.asyncio
#
#
# @pytest_asyncio.fixture(scope="session")
# async def client():
#     async with AsyncClient(app=app, base_url="http://test") as test_client:
#         yield test_client


# async def test_login_for_access_token(client):
#     # Используйте `client` напрямую без `async with`
#     response = await client.post(
#         "/token", data={"username": "user", "password": "password"}
#     )
#     assert response.status_code == 200


import httpx
import pytest
from httpx import AsyncClient

from main import app


@pytest.fixture
def client():
    return AsyncClient(app=app, base_url="http://testserver")
