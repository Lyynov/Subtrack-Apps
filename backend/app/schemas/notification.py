from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"
    IN_APP = "in_app"
    
class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    READ = "read"

class NotificationBase(BaseModel):
    type: NotificationType
    subject: str
    message: str
    subscription_id: Optional[int] = None
    status: NotificationStatus = NotificationStatus.PENDING
    scheduled_at: datetime

class NotificationCreate(NotificationBase):
    pass

class NotificationUpdate(BaseModel):
    type: Optional[NotificationType] = None
    subject: Optional[str] = None
    message: Optional[str] = None
    status: Optional[NotificationStatus] = None
    scheduled_at: Optional[datetime] = None

class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        orm_mode = True