import uuid

import pytest


@pytest.mark.asyncio
async def test_register_user(client):
    username = f"user_{uuid.uuid4()}"
    response = await client.post(
        "/register", json={"username": username, "password": "testpassword"}
    )
    assert response.status_code == 201
    assert response.json()["username"] == username

    # Попытка регистрации с существующим username
    response = await client.post(
        "/register", json={"username": username, "password": "newpassword"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Username is already taken"
