import time
from typing import Annotated
from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from passlib.context import CryptContext
from app.db.db import get_collection
from pymongo.collection import Collection as AsyncCollection
from app.schemas.user import User
from app.schemas.auth.token import Token
from app.services.auth.token import TokenService, get_token_service

oauth2 = OAuth2PasswordBearer(
    tokenUrl="auth/login",
    auto_error=False
)

crypt = CryptContext(
    schemes=['bcrypt'],
)

class AuthService:
    def __init__(
        self,
        users: Annotated[AsyncCollection, Depends(get_collection('users'))],
        token_service: Annotated[TokenService, Depends(get_token_service)]
    ):
        self.users = users
        self.token_service = token_service

    async def login(self, email: str, password: str) -> Token:
        user = await self.users.find_one({"email": email})
        
        if not user:
            raise HTTPException(
                status_code=400, detail="Email o contraseña incorrectos")

        if not crypt.verify(password, user["password"]):
            raise HTTPException(
                status_code=400, detail="Email o contraseña incorrectos")

        user_id = str(user["_id"])
        tokens = await self.token_service.create_tokens(user_id, user["email"])
        
        return tokens

    async def refresh_token(self, refresh_token: str) -> Token:
        return await self.token_service.refresh_access_token(refresh_token)

    async def logout(self, token: str):
        return await self.token_service.revoke_token(token)

    async def getUserByToken(self, token: Annotated[str, Depends(oauth2)]) -> User:
        exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de autenticación inválidas",
            headers={"WWW-Authenticate": "Bearer"})

        if not token:
            raise exception

        try:
            user_jwt = self.token_service.decode_token(token)
            if user_jwt.get("sub") is None:
                raise exception
            
            if await self.token_service.is_token_revoked(user_jwt.get("jti")):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token Invalido",
                    headers={"WWW-Authenticate": "Bearer"})
            
        except JWTError:
            raise exception

        user = await self.users.find_one({"_id": ObjectId(user_jwt.get("sub"))})
        
        if user is None:
            raise exception

        return User(
            id=str(user["_id"]),
            email=user["email"],
            full_name=user.get("full_name", ""),
            username=user.get("username", ""),
            avatar=user.get("avatar"),
            uid=user.get("uid"),
            provider=user.get("provider"),
            created_at=user.get("created_at", int(time.time()))
        )
    
    async def verify_user(self, token: Annotated[str, Depends(oauth2)]) -> User:
        user = await self.getUserByToken(token)
        return user

def get_auth_service(
    users: Annotated[AsyncCollection, Depends(get_collection('users'))],
    token_service: Annotated[TokenService, Depends(get_token_service)]
) -> AuthService:
    return AuthService(users, token_service)

async def get_authenticated_user(token: Annotated[str, Depends(oauth2)], auth_service: Annotated[AuthService, Depends(get_auth_service)]):
    return await auth_service.verify_user(token)