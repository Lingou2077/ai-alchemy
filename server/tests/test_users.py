from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient

from config import settings


async def login(client: AsyncClient, code: str = "mock-user-me") -> str:
    response = await client.post("/api/v1/auth/login", json={"code": code})
    assert response.status_code == 200
    return response.json()["token"]


@pytest.mark.asyncio
async def test_get_me_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_returns_profile(client: AsyncClient):
    token = await login(client, "mock-profile-user")
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["nickname"] == "炼金学徒"
    assert body["level"] == 1
    assert body["title"] == "见习炼金师"
    assert body["expProgress"]["totalExp"] == 0
    assert body["stats"]["totalQuizzes"] == 0


@pytest.mark.asyncio
async def test_patch_me_updates_nickname_and_avatar(client: AsyncClient):
    token = await login(client, "mock-patch-user")
    response = await client.patch(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "nickname": "Go 炼金师",
            "avatar_url": "https://example.com/avatar.png",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["nickname"] == "Go 炼金师"
    assert body["avatarUrl"] == "https://example.com/avatar.png"

    me = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.json()["nickname"] == "Go 炼金师"


@pytest.mark.asyncio
async def test_patch_me_rejects_empty_nickname(client: AsyncClient):
    token = await login(client, "mock-empty-nick")
    response = await client.patch(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"nickname": "   "},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_upload_avatar(client: AsyncClient):
    token = await login(client, "mock-upload-avatar")
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    response = await client.post(
        "/api/v1/users/me/avatar",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("avatar.png", png_bytes, "image/png")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["avatarUrl"].endswith(".png")
    assert "/uploads/avatars/" in body["avatarUrl"]


@pytest.mark.asyncio
async def test_upload_avatar_cos_mode(client: AsyncClient):
    settings.avatar_storage = "cos"
    settings.cos_avatar_prefix = "aialchemy/avatars"

    mock_storage = MagicMock()
    mock_storage.upload.return_value = (
        "https://yunpic-1348558641.cos.ap-guangzhou.myqcloud.com/aialchemy/avatars/5_test.png"
    )

    token = await login(client, "mock-upload-avatar-cos")
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    with patch("services.avatar_service.get_avatar_storage", return_value=mock_storage):
        response = await client.post(
            "/api/v1/users/me/avatar",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("avatar.png", png_bytes, "image/png")},
        )

    settings.avatar_storage = "local"

    assert response.status_code == 200
    body = response.json()
    assert body["avatarUrl"].startswith("https://")
    assert "/aialchemy/avatars/" in body["avatarUrl"]


@pytest.mark.asyncio
async def test_patch_me_rejects_local_avatar_path(client: AsyncClient):
    token = await login(client, "mock-local-avatar")
    response = await client.patch(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"avatar_url": "wxfile://tmp_avatar.png"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_users_are_isolated(client: AsyncClient):
    token_a = await login(client, "mock-isolated-a")
    token_b = await login(client, "mock-isolated-b")

    await client.patch(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"nickname": "用户 A"},
    )

    me_b = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert me_b.json()["nickname"] == "炼金学徒"
