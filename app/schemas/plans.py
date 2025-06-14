from pydantic import BaseModel, Field
from typing import Optional, Enum

from app.db.objectIdMongo import PyObjectId

class Plan(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    product_id: str
    price: int
    description: str
    created_at: int
