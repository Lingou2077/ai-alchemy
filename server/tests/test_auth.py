import pytest
from httpx import AsyncClient

from db.models.user import User


@pytest.mark.asyncio
async def test_login_creates_user_on_first_call(client: AsyncClient, db_session):
    response = await client.post("/api/v1/auth/login", json={"code": "mock-user-alpha"})
    assert response.status_code == 200
    body = response.json()
    assert body["token"]
    assert body["user"]["nickname"] == "炼金学徒"
    assert body["user"]["level"] == 1
    assert body["user"]["title"] == "见习炼金师"

    user = db_session.query(User).filter(User.openid == "mock_openid_mock-user-alpha").one()
    assert user.nickname == "炼金学徒"


@pytest.mark.asyncio
async def test_login_returns_same_user_on_repeat(client: AsyncClient, db_session):
    first = await client.post("/api/v1/auth/login", json={"code": "mock-user-beta"})
    second = await client.post("/api/v1/auth/login", json={"code": "mock-user-beta"})
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["user"]["id"] == second.json()["user"]["id"]
    assert db_session.query(User).count() == 1


@pytest.mark.asyncio
async def test_login_rejects_empty_code(client: AsyncClient):
    response = await client.post("/api/v1/auth/login", json={"code": ""})
    assert response.status_code == 400
