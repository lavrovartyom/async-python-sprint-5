import pytest


@pytest.mark.asyncio
async def test_login_for_access_token(client):
    async with client as async_client:
        response = await async_client.post(
            "/auth",
            data={"username": "testuser", "password": "testpassword"},
        )
    assert response.status_code == 200
    result = response.json()
    assert "access_token" in result
    assert result["token_type"] == "bearer"
