from pydantic import BaseModel, Field
from typing import Optional, Enum

from app.db.objectIdMongo import PyObjectId

class GuestStatus(str, Enum):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    DECLINED = 'declined'

class Guest(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    invitation_id: PyObjectId
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    status: GuestStatus = GuestStatus.PENDING
    responded_at: Optional[int] = None
    rsvp_token: str
    created_at: int

class GuestCreate(BaseModel):
    invitation_id: PyObjectId
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    rsvp_token: str

class GuestUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[GuestStatus] = None
    responded_at: Optional[int] = None 