from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

class BillingCycle(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMIANNUAL = "semiannual"
    ANNUAL = "annual"
    CUSTOM = "custom"

class SubscriptionBase(BaseModel):
    name: str
    description: Optional[str] = None
    amount: float = Field(..., gt=0)
    currency: str = "IDR"
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    billing_day: int = Field(..., ge=1, le=31)
    next_billing_date: date
    start_date: date = Field(default_factory=date.today)
    end_date: Optional[date] = None
    auto_renew: bool = True
    reminder_days: int = 3
    website_url: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True
    category_id: Optional[int] = None

class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = None
    billing_cycle: Optional[BillingCycle] = None
    billing_day: Optional[int] = Field(None, ge=1, le=31)
    next_billing_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    auto_renew: Optional[bool] = None
    reminder_days: Optional[int] = None
    website_url: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    category_id: Optional[int] = None

class Subscription(SubscriptionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class SubscriptionWithCategory(Subscription):
    category: Optional[dict] = None

class SubscriptionSummary(BaseModel):
    total_active: int
    total_amount_monthly: float
    total_amount_yearly: float
    upcoming_bills: List[Subscription]
    recently_added: List[Subscription]
    by_category: dict