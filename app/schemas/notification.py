from pydantic import BaseModel, Field
from typing import Optional, Enum

from app.db.objectIdMongo import PyObjectId

class NotificationType(str, Enum):
    INFO = 'info'
    SUCCESS = 'success'
    ERROR = 'error'

class Notification(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    user_id: PyObjectId
    message: str
    type: NotificationType = NotificationType.INFO
    is_read: bool = False
    created_at: int

class NotificationCreate(BaseModel):
    user_id: PyObjectId
    message: str
    type: NotificationType = NotificationType.INFO

class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None 