from datetime import UTC, datetime, timedelta

import jwt

from config import settings


def create_access_token(user_id: int) -> str:
    expire = datetime.now(UTC) + timedelta(seconds=settings.jwt_expire_seconds)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> int:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise ValueError("invalid token") from exc
    sub = payload.get("sub")
    if not sub:
        raise ValueError("invalid token")
    return int(sub)
