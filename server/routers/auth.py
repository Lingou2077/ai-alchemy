from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.session import get_db
from schemas.user import LoginRequest, LoginResponse, UserPublic
from services.auth_service import exchange_code_for_openid, get_or_create_user
from services.jwt_service import create_access_token
from services.user_service import serialize_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse, response_model_by_alias=True)
async def login(request: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    openid = await exchange_code_for_openid(request.code)
    user = get_or_create_user(db, openid)
    token = create_access_token(user.id)
    return LoginResponse(token=token, user=UserPublic.model_validate(serialize_user(user, db)))
