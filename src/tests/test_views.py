import uuid

import pytest
from httpx import AsyncClient


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


@pytest.mark.asyncio
async def test_download_file(client: AsyncClient):
    response = await client.post("/auth", data={"username": "test", "password": "test"})
    assert response.status_code == 200
    token_data = response.json()
    token = token_data["access_token"]

    file_meta_id = "ef3b3887-f336-42d8-ad2d-847222f9ae92"

    response = await client.get(
        f"/files/download?file_meta_id={file_meta_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert (
        response.headers["Content-Disposition"] == f"attachment; filename=testfile.txt"
    )

    expected_file_content = b"test file content"
    assert response.content == expected_file_content


@pytest.mark.asyncio
async def test_upload_file(client: AsyncClient):
    response = await client.post("/auth", data={"username": "test", "password": "test"})
    assert response.status_code == 200
    token_data = response.json()
    token = token_data["access_token"]

    file_content = b"test file content"
    files = {"file": ("testfile.txt", file_content, "text/plain")}
    params = {"path": "some/test/path"}

    response = await client.post(
        "/files/upload",
        headers={"Authorization": f"Bearer {token}"},
        files=files,
        params=params,
    )

    assert response.status_code == 200, response.text
    response_data = response.json()
    assert "id" in response_data
    assert response_data["name"] == "testfile.txt"


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


@pytest.mark.asyncio
async def test_get_files(client: AsyncClient):
    test_username = "test"
    test_password = "test"

    response = await client.post(
        "/auth", data={"username": test_username, "password": test_password}
    )
    assert response.status_code == 200
    token_data = response.json()
    test_token = token_data["access_token"]

    headers = {"Authorization": f"Bearer {test_token}"}
    response = await client.get("/files/", headers=headers)
    assert response.status_code == 200
    assert "account_id" in response.json()
    assert "files" in response.json()
