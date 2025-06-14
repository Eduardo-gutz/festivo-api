import time
import uuid
from typing import Annotated
from fastapi import Depends, HTTPException
from app.core.globals import SECRET_KEY, ALGORITHM
from app.db.db import get_collection
from pymongo.collection import Collection as AsyncCollection
from jose import jwt, JWTError
from app.schemas.auth.token import TokenPayload

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

    async def create_token(self, user_id: str, user_email: str) -> str:
        jti = str(uuid.uuid4())
        token_data = TokenPayload(
            sub=user_id,
            email=user_email,
            exp=int(time.time()) + (3600 * 2),
            jti=jti
        )
        await self.tokens.insert_one(token_data.model_dump())
        
        return jwt.encode(token_data.model_dump(), self.SECRET_KEY, algorithm=self.ALGORITHM)

    def decode_token(self, token: str) -> dict:
        return jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])

    async def is_token_revoked(self, jti: str) -> bool:
        token = await self.revoked_tokens.find_one({"jti": jti})
        return token is not None

    async def revoke_token(self, token: str):
        try:
            payload = jwt.decode(token, self.SECRET_KEY,
                             algorithms=[self.ALGORITHM])
            await self.revoked_tokens.insert_one({"jti": payload["jti"], "revoked_at": int(time.time())})
            return {"message": "Token revocado exitosamente"}
        except JWTError:
            raise HTTPException(status_code=400, detail="Token inválido")

    async def cleanup_expired_tokens(self):
        current_time = int(time.time())
        await self.revoked_tokens.delete_many({"revoked_at": {"$lt": current_time - 3600 * 2}})


def get_token_service(
    tokens: Annotated[AsyncCollection, Depends(get_collection('tokens'))],
    revoked_tokens: Annotated[AsyncCollection, Depends(get_collection('revoked_tokens'))]
) -> TokenService:
    return TokenService(tokens, revoked_tokens)