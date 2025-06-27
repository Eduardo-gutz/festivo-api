from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    email: Optional[str] = None
    exp: Optional[datetime] = None
    jti: Optional[str] = None


class RevokedToken(BaseModel):
    jti: str = Field(..., description="Identificador único del token")
    exp: datetime = Field(..., description="Fecha de expiración del token")
    revoked_at: datetime = Field(default_factory=datetime.utcnow)
