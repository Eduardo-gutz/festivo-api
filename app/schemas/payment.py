from pydantic import BaseModel, Field
from typing import Optional, Enum

from app.db.objectIdMongo import PyObjectId

class PaymentMethod(str, Enum):
    STRIPE = 'stripe'
    PAYPAL = 'paypal'

class PaymentStatus(str, Enum):
    COMPLETED = 'completed'
    FAILED = 'failed'
    PENDING = 'pending'

class Payment(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    user_id: PyObjectId
    plan_id: PyObjectId
    amount: float
    payment_method: PaymentMethod
    payment_reference: str
    paid_at: int
    status: PaymentStatus

class PaymentCreate(BaseModel):
    user_id: PyObjectId
    plan_id: PyObjectId
    amount: float
    payment_method: PaymentMethod
    payment_reference: str
    status: PaymentStatus = PaymentStatus.PENDING

class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    paid_at: Optional[int] = None 