from typing import Annotated
from fastapi import APIRouter, Depends, Body
from app.schemas.user import UserCreateByPassword
from app.schemas.auth.token import Token
from app.services.users.user import UserService, get_user_service
from app.services.auth.auth import AuthService, get_auth_service
from app.services.auth.token import TokenService, get_token_service
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

oauth2 = OAuth2PasswordBearer(
    tokenUrl="auth/login",
    auto_error=False
)

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/login", response_model=Token)
async def login(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    auth: OAuth2PasswordRequestForm = Depends()
):
    return await auth_service.login(auth.username, auth.password)

@router.post("/refresh", response_model=Token)
async def refresh_token(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    refresh_token: str = Body(..., embed=True)
):
    return await auth_service.refresh_token(refresh_token)

@router.post("/register", response_model=Token)
async def register(
    user_service: Annotated[UserService, Depends(get_user_service)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    user: UserCreateByPassword
):
    new_user = await user_service.create_user(user)
    response = await auth_service.login(new_user.email, user.password)
    return response


@router.post("/logout")
async def logout(
    token: Annotated[str, Depends(oauth2)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    return await auth_service.logout(token) 