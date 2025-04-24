from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.database import get_db
from app.db.models import Notification, NotificationStatus, User
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationUpdate,
)
from app.services.notification_service import (
    create_notification,
    get_notifications_by_user,
    get_notification_by_id,
    update_notification,
    delete_notification,
    mark_notification_as_read,
)

router = APIRouter()

@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_new_notification(
    notification: NotificationCreate, 
    db: Session = Depends(get_db),
    # In a real implementation, use authentication to get the current user
    # For now we'll use a placeholder user_id
    user_id: int = 1
):
    """
    Create a new notification.
    """
    return create_notification(db=db, notification=notification, user_id=user_id)

@router.get("/", response_model=List[NotificationResponse])
def read_notifications(
    skip: int = 0, 
    limit: int = 100, 
    status: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    # In a real implementation, use authentication to get the current user
    user_id: int = 1
):
    """
    Retrieve notifications for a user.
    """
    notifications = get_notifications_by_user(
        db, 
        user_id=user_id, 
        skip=skip, 
        limit=limit,
        status=status,
        from_date=from_date,
        to_date=to_date
    )
    return notifications

@router.get("/{notification_id}", response_model=NotificationResponse)
def read_notification(
    notification_id: int = Path(..., title="The ID of the notification to get"),
    db: Session = Depends(get_db),
    # In a real implementation, use authentication to get the current user
    user_id: int = 1
):
    """
    Get a specific notification by id.
    """
    notification = get_notification_by_id(db, notification_id=notification_id, user_id=user_id)
    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Notification not found"
        )
    return notification

@router.put("/{notification_id}", response_model=NotificationResponse)
def update_notification_info(
    notification_id: int,
    notification: NotificationUpdate,
    db: Session = Depends(get_db),
    # In a real implementation, use authentication to get the current user
    user_id: int = 1
):
    """
    Update a notification.
    """
    db_notification = get_notification_by_id(db, notification_id=notification_id, user_id=user_id)
    if db_notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Notification not found"
        )
    return update_notification(db=db, notification_id=notification_id, notification=notification)

@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification_by_id(
    notification_id: int,
    db: Session = Depends(get_db),
    # In a real implementation, use authentication to get the current user
    user_id: int = 1
):
    """
    Delete a notification.
    """
    db_notification = get_notification_by_id(db, notification_id=notification_id, user_id=user_id)
    if db_notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Notification not found"
        )
    delete_notification(db=db, notification_id=notification_id)
    return None

@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    # In a real implementation, use authentication to get the current user
    user_id: int = 1
):
    """
    Mark a notification as read.
    """
    db_notification = get_notification_by_id(db, notification_id=notification_id, user_id=user_id)
    if db_notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Notification not found"
        )
    return mark_notification_as_read(db=db, notification_id=notification_id)

@router.post("/upcoming-reminders", status_code=status.HTTP_200_OK)
def generate_upcoming_reminders(
    days_ahead: int = Query(7, description="Number of days ahead to generate reminders for"),
    db: Session = Depends(get_db)
):
    """
    Generate upcoming subscription reminders.
    This endpoint would typically be called by a scheduled job.
    """
    # This would be implemented in a real service to scan for upcoming subscriptions
    # and create notifications for them
    return {"message": f"Reminders generated for subscriptions due in the next {days_ahead} days"}