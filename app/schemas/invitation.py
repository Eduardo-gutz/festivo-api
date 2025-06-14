from pydantic import BaseModel, Field
from typing import Optional, Enum
from datetime import datetime

from app.db.objectIdMongo import PyObjectId

class EventType(str, Enum):
    WEDDING = 'wedding'
    BIRTHDAY = 'birthday'
    ANNIVERSARY = 'anniversary'
    BABY_SHOWER = 'baby_shower'
    GRADUATION = 'graduation'
    OTHER = 'other'

class AnimationType(str, Enum):
    FADE = 'fade'
    SLIDE = 'slide'
    ZOOM = 'zoom'
    NONE = 'none'

class Invitation(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    user_id: PyObjectId
    title: str
    event_type: EventType
    template_id: PyObjectId
    custom_text: str
    background_image_url: str
    music_url: Optional[str] = None
    animation_type: Optional[AnimationType] = None
    is_published: bool = False
    published_url: Optional[str] = None
    qr_code_url: Optional[str] = None
    created_at: int
    updated_at: int

class InvitationCreate(BaseModel):
    title: str
    event_type: EventType
    template_id: PyObjectId
    custom_text: str
    background_image_url: str
    music_url: Optional[str] = None
    animation_type: Optional[AnimationType] = None

class InvitationUpdate(BaseModel):
    title: Optional[str] = None
    event_type: Optional[EventType] = None
    template_id: Optional[PyObjectId] = None
    custom_text: Optional[str] = None
    background_image_url: Optional[str] = None
    music_url: Optional[str] = None
    animation_type: Optional[AnimationType] = None
    is_published: Optional[bool] = None
