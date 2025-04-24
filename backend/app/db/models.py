from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, Date, DateTime, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from datetime import datetime

Base = declarative_base()

class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"

class BillingCycle(enum.Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMIANNUAL = "semiannual"
    ANNUAL = "annual"
    CUSTOM = "custom"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.USER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    subscriptions = relationship("Subscription", back_populates="user")
    categories = relationship("Category", back_populates="user")
    notifications = relationship("Notification", back_populates="user")

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    color = Column(String, default="#1E90FF")  # Default color code
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="categories")
    subscriptions = relationship("Subscription", back_populates="category")

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    amount = Column(Float)
    currency = Column(String, default="IDR")
    billing_cycle = Column(Enum(BillingCycle), default=BillingCycle.MONTHLY)
    billing_day = Column(Integer)  # Day of month/quarter/year when billing occurs
    next_billing_date = Column(Date)
    start_date = Column(Date, default=datetime.now().date())
    end_date = Column(Date, nullable=True)  # For fixed-term subscriptions
    auto_renew = Column(Boolean, default=True)
    reminder_days = Column(Integer, default=3)  # Days before billing to send reminder
    website_url = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    user_id = Column(Integer, ForeignKey("users.id"))
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="subscriptions")
    category = relationship("Category", back_populates="subscriptions")
    payment_history = relationship("PaymentHistory", back_populates="subscription")
    notifications = relationship("Notification", back_populates="subscription")

class PaymentHistory(Base):
    __tablename__ = "payment_history"
    
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    payment_date = Column(Date)
    amount = Column(Float)
    status = Column(String)  # "paid", "pending", "failed"
    payment_method = Column(String, nullable=True)
    receipt_url = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    subscription = relationship("Subscription", back_populates="payment_history")

class NotificationType(enum.Enum):
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"
    IN_APP = "in_app"

class NotificationStatus(enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    READ = "read"

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    type = Column(Enum(NotificationType))
    subject = Column(String)
    message = Column(Text)
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING)
    scheduled_at = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="notifications")
    subscription = relationship("Subscription", back_populates="notifications")