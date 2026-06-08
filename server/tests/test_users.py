import pytest
from httpx import AsyncClient


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
