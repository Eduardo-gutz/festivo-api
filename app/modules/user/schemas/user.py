from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

from app.db.objectIdMongo import PyObjectId

class Provider(str, Enum):
    PASSWORD = 'password'
    GOOGLE = 'google'
    
class Role(str, Enum):
    ADMIN = 'admin'
    USER = 'user'
    PUBLISHER = 'publisher'

class User(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    username: str
    full_name: str
    avatar: Optional[str] = None
    email: str
    uid: Optional[str] = None
    provider: Optional[Provider] = Provider.PASSWORD
    created_at: int
    verify_email: Optional[bool] = False
    role: Optional[Role] = Role.USER

class UserCreate(BaseModel):
    full_name: str
    email: str
    username: str
    provider: Optional[Provider] = Provider.PASSWORD
    token: Optional[str] = None

class UserUpdate(User):
    password: Optional[str] = None
    uid: Optional[str] = None
    verify_email: Optional[bool] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
    
class UserMinimal(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    username: str
    full_name: str
    avatar: Optional[str] = None
