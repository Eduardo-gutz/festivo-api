from pydantic import BaseModel, Field
from typing import Optional, Enum

from app.db.objectIdMongo import PyObjectId

class FileType(str, Enum):
    IMAGE = 'image'
    MUSIC = 'music'

class File(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    user_id: PyObjectId
    file_type: FileType
    url: str
    size_in_kb: float
    uploaded_at: int

class FileCreate(BaseModel):
    user_id: PyObjectId
    file_type: FileType
    url: str
    size_in_kb: float

class FileUpdate(BaseModel):
    url: Optional[str] = None
    size_in_kb: Optional[float] = None 