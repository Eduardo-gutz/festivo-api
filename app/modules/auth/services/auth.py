import time
from typing import Annotated
from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError
from firebase_admin import auth
from passlib.context import CryptContext
from app.db.db import get_collection
from pymongo.collection import Collection as AsyncCollection
from app.modules.user.schemas.user import User
from app.modules.auth.schemas.token import Token
from app.core.utils.error_codes import ErrorCodes
from app.modules.auth.services.token import TokenService, get_token_service

oauth2 = OAuth2PasswordBearer(
    tokenUrl="auth/login",
    auto_error=False,
    scopes={
        "admin": "Admin",
        "user": "User",
        "publisher": "Publisher"
    }
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
                status_code=400, detail=ErrorCodes.INVALID_CREDENTIALS)

        if not crypt.verify(password, user["password"]):
            raise HTTPException(
                status_code=400, detail=ErrorCodes.INVALID_CREDENTIALS)

        user_id = str(user["_id"])
        tokens = await self.token_service.create_tokens(user_id, user["email"])
        
        return tokens

    async def login_with_firebase(self, firebase_token: str) -> Token:
        try:
            decoded_token = auth.verify_id_token(firebase_token)
            
            uid = decoded_token.get("uid")
            email = decoded_token.get("email")
            
            if not email:
                raise HTTPException(
                    status_code=400, detail=ErrorCodes.INVALID_EMAIL)
            
            user = await self.users.find_one({"uid": uid, "email": email})
            
            if not user:
               raise HTTPException(
                    status_code=400, detail=ErrorCodes.INVALID_EMAIL)
            
            user_id = str(user["_id"])
            tokens = await self.token_service.create_tokens(user_id, email)
            return tokens
            
        except auth.InvalidIdTokenError:
            raise HTTPException(
                status_code=401, detail=ErrorCodes.INVALID_TOKEN)

    async def refresh_token(self, refresh_token: str) -> Token:
        return await self.token_service.refresh_access_token(refresh_token)

    async def getUserByToken(self, token: Annotated[str, Depends(oauth2)]) -> User:
        exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorCodes.INVALID_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"})

        if not token:
            raise exception

        try:
            user_jwt = self.token_service.decode_token(token)
            sub = user_jwt.get("sub")
            
            if sub is None:
                raise exception
            
        except JWTError:
            raise exception

        user = await self.users.find_one({"_id": ObjectId(sub)})
        
        if user is None:
            raise exception

        return User(
            _id=user["_id"],
            email=user["email"],
            full_name=user.get("full_name", ""),
            username=user.get("username", ""),
            avatar=user.get("avatar"),
            uid=user.get("uid"),
            provider=user.get("provider"),
            created_at=user.get("created_at", int(time.time())),
            role=user.get("role")
        )
    
    async def verify_user(self, security_scopes: SecurityScopes, token: Annotated[str, Depends(oauth2)]) -> User:
        user = await self.getUserByToken(token)
        
        if security_scopes.scopes:
            if user.role not in security_scopes.scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=ErrorCodes.NOT_AUTHORIZED
                )
        
        return user

def get_auth_service(
    users: Annotated[AsyncCollection, Depends(get_collection('users'))],
    token_service: Annotated[TokenService, Depends(get_token_service)]
) -> AuthService:
    return AuthService(users, token_service)

async def get_authenticated_user(security_scopes: SecurityScopes, token: Annotated[str, Depends(oauth2)], auth_service: Annotated[AuthService, Depends(get_auth_service)]):
    return await auth_service.verify_user(security_scopes, token)
