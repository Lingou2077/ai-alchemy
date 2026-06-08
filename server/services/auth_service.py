import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from config import settings
from db.models.user import User
from services.exp_config import level_for_exp


async def exchange_code_for_openid(code: str) -> str:
    normalized = code.strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="登录 code 不能为空")

    if settings.dev_mock_login:
        return f"mock_openid_{normalized}"

    if not settings.wechat_app_id or not settings.wechat_app_secret:
        raise HTTPException(status_code=503, detail="微信登录未配置")

    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.wechat_app_id,
        "secret": settings.wechat_app_secret,
        "js_code": normalized,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url, params=params)
        data = response.json()

    if data.get("errcode"):
        raise HTTPException(status_code=401, detail="微信登录失败，请重试")

    openid = data.get("openid")
    if not openid:
        raise HTTPException(status_code=401, detail="微信登录失败，请重试")
    return openid


def get_or_create_user(db: Session, openid: str) -> User:
    user = db.query(User).filter(User.openid == openid).one_or_none()
    if user is not None:
        return user

    level, title = level_for_exp(0)
    user = User(
        openid=openid,
        nickname="炼金学徒",
        avatar_url="",
        exp=0,
        level=level,
        title=title,
        total_quizzes=0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
