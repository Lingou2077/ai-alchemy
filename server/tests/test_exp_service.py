import pytest
from httpx import AsyncClient

from db.models.user import User
from services.exp_service import settle_exp


@pytest.mark.asyncio
async def test_settle_exp_success_bonus(db_session, sample_user_factory):
    user = sample_user_factory(exp=0)
    result = settle_exp(db_session, user, "exp-s1", "completed")
    assert result["amount"] == 15
    assert user.exp == 15
    assert result["leveledUp"] is False


@pytest.mark.asyncio
async def test_settle_exp_failed_only_base(db_session, sample_user_factory):
    user = sample_user_factory(exp=0)
    result = settle_exp(db_session, user, "exp-s2", "failed")
    assert result["amount"] == 10
    assert user.exp == 10


@pytest.mark.asyncio
async def test_settle_exp_idempotent(db_session, sample_user_factory):
    user = sample_user_factory(exp=0)
    first = settle_exp(db_session, user, "exp-s3", "completed")
    second = settle_exp(db_session, user, "exp-s3", "completed")
    assert first["amount"] == 15
    assert second["amount"] == 15
    assert user.exp == 15


@pytest.mark.asyncio
async def test_settle_exp_level_up(db_session, sample_user_factory):
    user = sample_user_factory(exp=25)
    result = settle_exp(db_session, user, "exp-s4", "completed")
    assert result["amount"] == 15
    assert result["leveledUp"] is True
    assert user.level >= 2
