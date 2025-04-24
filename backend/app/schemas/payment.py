from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

class PaymentBase(BaseModel):
    subscription_id: int
    payment_date: date
    amount: float = Field(..., gt=0)
    status: str = "paid"  # "paid", "pending", "failed"
    payment_method: Optional[str] = None
    receipt_url: Optional[str] = None
    notes: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(BaseModel):
    payment_date: Optional[date] = None
    amount: Optional[float] = Field(None, gt=0)
    status: Optional[str] = None
    payment_method: Optional[str] = None
    receipt_url: Optional[str] = None
    notes: Optional[str] = None

class Payment(PaymentBase):
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

class PaymentWithSubscription(Payment):
    subscription_name: str
    category_name: Optional[str] = None
    category_color: Optional[str] = None