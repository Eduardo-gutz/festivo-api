import re
import time
from typing import Annotated
from fastapi import Depends, HTTPException
from passlib.context import CryptContext
from pymongo.collection import Collection as AsyncCollection

from app.db.db import get_collection
from app.schemas.user import User, UserCreateByPassword

crypt = CryptContext(schemes=['bcrypt'])

class UserService:
    def __init__(self, users: Annotated[AsyncCollection, Depends(get_collection('users'))]):
        self.users = users

    async def create_user(self, user: UserCreateByPassword):
        already_email = await self.users.find_one({"email": user.email})
        if already_email:
            raise HTTPException(status_code=400, detail="Email ya registrado")
        
        is_valid_email = re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", user.email)
        is_valid_password = re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", user.password)
        
        if not is_valid_email:
            raise HTTPException(status_code=400, detail="Email Invalido")
        if not is_valid_password:
            raise HTTPException(status_code=400, detail="Contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula, un número y un carácter especial")
        
        db_user ={
            "email": user.email,
            "full_name": user.full_name,
            "created_at": int(time.time()),
            "password": crypt.hash(user.password),
            "provider": user.provider,
            "username": user.username
        }
        
        await self.users.insert_one(db_user)
        
        return User.model_validate(db_user)

def get_user_service(
    users: Annotated[AsyncCollection, Depends(get_collection('users'))]
) -> UserService:
    return UserService(users)
