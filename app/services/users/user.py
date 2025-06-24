import re
import time
from typing import Annotated
from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from pymongo.collection import Collection as AsyncCollection

from app.db.db import get_collection
from app.schemas.user import User, UserCreate
from firebase_admin import auth
from app.core.utils.error_codes import ErrorCodes

crypt = CryptContext(schemes=['bcrypt'])


class UserService:
    def __init__(self, users: Annotated[AsyncCollection, Depends(get_collection('users'))]):
        self.users = users

    async def create_user(self, user: UserCreate):
        try:
            decoded_token = auth.verify_id_token(user.token)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCodes.INVALID_TOKEN
            )

        is_valid_email = re.match(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", user.email)

        if not is_valid_email:
            raise HTTPException(status_code=400, detail=ErrorCodes.INVALID_EMAIL)
        
        already_email = await self.users.find_one({"email": user.email})
        if already_email:
            raise HTTPException(status_code=400, detail=ErrorCodes.EMAIL_ALREADY_REGISTERED)

        db_user = {
            "uid": decoded_token.get("uid"),
            "email": user.email,
            "full_name": user.full_name,
            "created_at": int(time.time()),
            "provider": user.provider,
            "username": user.username
        }

        await self.users.insert_one(db_user)
        return User.model_validate(db_user)


def get_user_service(
    users: Annotated[AsyncCollection, Depends(get_collection('users'))]
) -> UserService:
    return UserService(users)
