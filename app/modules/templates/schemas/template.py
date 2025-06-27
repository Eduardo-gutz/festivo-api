from pydantic import BaseModel, Field
from typing import Optional, Any

from app.db.objectIdMongo import PyObjectId
from app.modules.user.schemas.user import UserMinimal

class Template(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    name: str
    description: str
    preview_image_url: str
    is_premium: bool
    created_at: int
    updated_at: int
    elements: list[Any]
    user: Optional[UserMinimal] = None

class TemplateMinimal(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    name: str
    description: str
    preview_image_url: str
    is_premium: bool
    
class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    preview_image_url: Optional[str] = None
    is_premium: Optional[bool] = None
    elements: Optional[list[Any]] = None