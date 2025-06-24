import time
import uuid
from typing import Annotated, Dict
from fastapi import Depends, HTTPException
from app.core.globals import SECRET_KEY, ALGORITHM
from app.db.db import get_collection
from pymongo.collection import Collection as AsyncCollection
from jose import jwt, JWTError
from app.schemas.auth.token import TokenPayload, Token
from app.core.utils.error_codes import ErrorCodes

ACCESS_TOKEN_EXPIRE_MINUTES = 1
REFRESH_TOKEN_EXPIRE_DAYS = 7

class TokenService:
    def __init__(
        self,
        tokens: Annotated[AsyncCollection, Depends(get_collection('tokens'))],
        revoked_tokens: Annotated[AsyncCollection, Depends(get_collection('revoked_tokens'))]
    ):
        self.tokens = tokens
        self.revoked_tokens = revoked_tokens
        self.SECRET_KEY = SECRET_KEY
        self.ALGORITHM = ALGORITHM

    async def create_tokens(self, user_id: str, user_email: str) -> Token:
        access_jti = str(uuid.uuid4())
        access_expires = int(time.time()) + (ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        access_token_data = TokenPayload(
            sub=user_id,
            email=user_email,
            exp=access_expires,
            jti=access_jti
        )
        
        refresh_jti = str(uuid.uuid4())
        refresh_expires = int(time.time()) + (REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)
        refresh_token_data = TokenPayload(
            sub=user_id,
            email=user_email,
            exp=refresh_expires,
            jti=refresh_jti
        )
        
        access_token = jwt.encode(access_token_data.model_dump(), self.SECRET_KEY, algorithm=self.ALGORITHM)
        refresh_token = jwt.encode(refresh_token_data.model_dump(), self.SECRET_KEY, algorithm=self.ALGORITHM)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    def decode_token(self, token: str) -> dict:
        return jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])

    async def refresh_access_token(self, refresh_token: str) -> Token:
        try:
            payload = self.decode_token(refresh_token)
            
            current_time = int(time.time())
            if payload.get("exp") and current_time > payload.get("exp"):
                raise HTTPException(status_code=401, detail=ErrorCodes.INVALID_TOKEN)
            
            user_id = payload.get("sub")
            user_email = payload.get("email")
            
            if not user_id or not user_email:
                raise HTTPException(status_code=401, detail=ErrorCodes.INVALID_TOKEN)
                
            return await self.create_tokens(user_id, user_email)
            
        except JWTError:
            raise HTTPException(status_code=401, detail=ErrorCodes.INVALID_TOKEN)


def get_token_service(
    tokens: Annotated[AsyncCollection, Depends(get_collection('tokens'))],
    revoked_tokens: Annotated[AsyncCollection, Depends(get_collection('revoked_tokens'))]
) -> TokenService:
    return TokenService(tokens, revoked_tokens)