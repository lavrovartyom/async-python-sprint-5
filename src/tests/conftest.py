import pytest
from httpx import AsyncClient

from main import app


@pytest.fixture
def client():
    return AsyncClient(app=app, base_url="http://testserver")
