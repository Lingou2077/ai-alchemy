from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from db.models.user import User
from db.session import get_db
from services.jwt_service import decode_access_token


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.strip().split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    return token or None


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
) -> User:
    token = _extract_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="未登录")
    try:
        user_id = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录") from exc

    user = db.query(User).filter(User.id == user_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


def get_optional_user(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
) -> User | None:
    token = _extract_bearer_token(authorization)
    if not token:
        return None
    try:
        user_id = decode_access_token(token)
    except ValueError:
        return None
    return db.query(User).filter(User.id == user_id).one_or_none()
