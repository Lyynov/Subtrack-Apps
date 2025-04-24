from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.models import Notification, NotificationStatus, Subscription
from app.schemas.notification import NotificationCreate, NotificationUpdate

def get_notification_by_id(db: Session, notification_id: int, user_id: int) -> Optional[Notification]:
    """
    Get a notification by ID for a specific user
    """
    return db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()

def get_notifications_by_user(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100,
    status: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None
) -> List[Notification]:
    """
    Get notifications for a user with optional filters
    """
    # Base query
    query = db.query(Notification).filter(Notification.user_id == user_id)
    
    # Apply filters
    if status:
        query = query.filter(Notification.status == status)
    
    if from_date:
        query = query.filter(Notification.scheduled_at >= from_date)
    
    if to_date:
        query = query.filter(Notification.scheduled_at <= to_date)
    
    # Order by scheduled date
    query = query.order_by(Notification.scheduled_at.desc())
    
    # Apply pagination
    return query.offset(skip).limit(limit).all()

def create_notification(
    db: Session, 
    notification: NotificationCreate, 
    user_id: int
) -> Notification:
    """
    Create a new notification
    """
    # Check if subscription exists if specified
    if notification.subscription_id:
        subscription = db.query(Subscription).filter(
            Subscription.id == notification.subscription_id,
            Subscription.user_id == user_id
        ).first()
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
    
    # Create the notification object
    db_notification = Notification(
        **notification.dict(),
        user_id=user_id
    )
    
    # Add to database
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    
    return db_notification

def update_notification(
    db: Session, 
    notification_id: int, 
    notification: NotificationUpdate
) -> Notification:
    """
    Update an existing notification
    """
    # Get the notification
    db_notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()
    
    if not db_notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Notification not found"
        )
    
    # Update notification fields
    update_data = notification.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_notification, key, value)
    
    # Commit changes
    db.commit()
    db.refresh(db_notification)
    
    return db_notification

def delete_notification(db: Session, notification_id: int) -> None:
    """
    Delete a notification
    """
    # Get the notification
    db_notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()
    
    if not db_notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Notification not found"
        )
    
    # Delete the notification
    db.delete(db_notification)
    db.commit()

def mark_notification_as_read(db: Session, notification_id: int) -> Notification:
    """
    Mark a notification as read
    """
    # Get the notification
    db_notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()
    
    if not db_notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Notification not found"
        )
    
    # Update status and read_at
    db_notification.status = NotificationStatus.READ
    db_notification.read_at = datetime.now()
    
    # Commit changes
    db.commit()
    db.refresh(db_notification)
    
    return db_notification

def mark_notification_as_sent(db: Session, notification_id: int) -> Notification:
    """
    Mark a notification as sent
    """
    # Get the notification
    db_notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()
    
    if not db_notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Notification not found"
        )
    
    # Update status and sent_at
    db_notification.status = NotificationStatus.SENT
    db_notification.sent_at = datetime.now()
    
    # Commit changes
    db.commit()
    db.refresh(db_notification)
    
    return db_notification

def create_subscription_reminder(
    db: Session,
    subscription: Subscription,
    days_before: int = 3
) -> Notification:
    """
    Create a reminder notification for an upcoming subscription payment
    """
    # Calculate the date when the notification should be sent
    notification_date = subscription.next_billing_date - timedelta(days=days_before)
    
    # Create notification message
    subject = f"{subscription.name} subscription reminder"
    message = (
        f"Your {subscription.name} subscription will be renewed in {days_before} "
        f"days on {subscription.next_billing_date.strftime('%Y-%m-%d')} "
        f"for {subscription.currency} {subscription.amount:,.0f}."
    )
    
    # Create the notification
    notification = NotificationCreate(
        type="email",  # Default to email, could be configurable
        subject=subject,
        message=message,
        subscription_id=subscription.id,
        status=NotificationStatus.PENDING,
        scheduled_at=datetime.combine(notification_date, datetime.min.time())
    )
    
    return create_notification(db, notification, subscription.user_id)

def generate_subscription_reminders(
    db: Session,
    days_ahead: int = 7,
    default_reminder_days: int = 3
) -> List[Notification]:
    """
    Generate reminders for all subscriptions that will be due in the next X days
    """
    created_notifications = []
    
    # Get the date range
    today = datetime.now().date()
    future_date = today + timedelta(days=days_ahead)
    
    # Find subscriptions due in this range
    subscriptions = db.query(Subscription).filter(
        Subscription.is_active == True,
        Subscription.next_billing_date.between(today, future_date)
    ).all()
    
    # Create notifications for each subscription
    for subscription in subscriptions:
        # Use the subscription's reminder_days or the default
        reminder_days = subscription.reminder_days or default_reminder_days
        
        # Skip if the reminder date has already passed
        reminder_date = subscription.next_billing_date - timedelta(days=reminder_days)
        if reminder_date < today:
            continue
        
        # Skip if a similar notification already exists
        existing = db.query(Notification).filter(
            Notification.subscription_id == subscription.id,
            Notification.status.in_([NotificationStatus.PENDING, NotificationStatus.SENT]),
            Notification.scheduled_at > datetime.now() - timedelta(days=1)
        ).first()
        
        if existing:
            continue
        
        # Create the reminder
        notification = create_subscription_reminder(db, subscription, reminder_days)
        created_notifications.append(notification)
    
    return created_notifications