from pydantic import BaseModel, Field
from typing import Optional, Any

from app.db.objectIdMongo import PyObjectId

class Template(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    name: str
    description: str
    preview_image_url: str
    is_premium: bool
    created_at: int
    updated_at: int
    elements: list[Any]
