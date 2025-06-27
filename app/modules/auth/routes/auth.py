from typing import Annotated
from fastapi import APIRouter, Depends, Body
from app.modules.auth.services.auth import AuthService, get_auth_service
from app.modules.user.schemas.user import UserCreate
from app.modules.auth.schemas.token import Token
from app.modules.user.services.user import UserService, get_user_service
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/login", response_model=Token)
async def login(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    auth: OAuth2PasswordRequestForm = Depends()
):
    return await auth_service.login_with_firebase(auth.password)

@router.post("/login/token", response_model=Token)
async def login_with_firebase(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    token: str = Body(..., embed=True)
):
    return await auth_service.login_with_firebase(token)

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
    user: UserCreate
):
    await user_service.create_user(user)
    response = await auth_service.login_with_firebase(user.token)
    return response
