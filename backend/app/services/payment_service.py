from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import date, datetime

from app.db.models import PaymentHistory, Subscription
from app.schemas.payment import PaymentCreate, PaymentUpdate
from app.services.subscription_service import get_subscription_by_id, update_next_billing_date

def get_payment_by_id(db: Session, payment_id: int) -> Optional[PaymentHistory]:
    """
    Get a payment by ID
    """
    return db.query(PaymentHistory).filter(PaymentHistory.id == payment_id).first()

def get_payments_by_subscription(
    db: Session, 
    subscription_id: int, 
    user_id: int,
    skip: int = 0, 
    limit: int = 100
) -> List[PaymentHistory]:
    """
    Get payments for a specific subscription
    """
    # Check if subscription exists and belongs to user
    subscription = get_subscription_by_id(db, subscription_id, user_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Get payments
    return db.query(PaymentHistory).filter(
        PaymentHistory.subscription_id == subscription_id
    ).order_by(PaymentHistory.payment_date.desc()).offset(skip).limit(limit).all()

def get_payments_by_user(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[str] = None
) -> List[PaymentHistory]:
    """
    Get payments for a user with optional filters
    """
    # Base query to get user's subscriptions first
    subscriptions = db.query(Subscription).filter(
        Subscription.user_id == user_id
    ).all()
    
    if not subscriptions:
        return []
    
    # Get subscription IDs
    subscription_ids = [sub.id for sub in subscriptions]
    
    # Base query for payments
    query = db.query(PaymentHistory).filter(
        PaymentHistory.subscription_id.in_(subscription_ids)
    )
    
    # Apply filters
    if start_date:
        query = query.filter(PaymentHistory.payment_date >= start_date)
    
    if end_date:
        query = query.filter(PaymentHistory.payment_date <= end_date)
    
    if status:
        query = query.filter(PaymentHistory.status == status)
    
    # Apply sorting and pagination
    return query.order_by(PaymentHistory.payment_date.desc()).offset(skip).limit(limit).all()

def create_payment(db: Session, payment: PaymentCreate, user_id: int) -> PaymentHistory:
    """
    Create a new payment record
    """
    # Check if subscription exists and belongs to user
    subscription = get_subscription_by_id(db, payment.subscription_id, user_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Create the payment object
    db_payment = PaymentHistory(
        **payment.dict()
    )
    
    # Add to database
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    
    # If payment is marked as paid, update the next billing date
    if payment.status == "paid":
        update_next_billing_date(db, payment.subscription_id, user_id)
    
    return db_payment

def update_payment(db: Session, payment_id: int, payment: PaymentUpdate, user_id: int) -> PaymentHistory:
    """
    Update an existing payment
    """
    # Get the payment
    db_payment = get_payment_by_id(db, payment_id)
    if not db_payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # Check if subscription belongs to user
    subscription = get_subscription_by_id(db, db_payment.subscription_id, user_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Track old status
    old_status = db_payment.status
    
    # Update payment fields
    update_data = payment.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_payment, key, value)
    
    # Commit changes
    db.commit()
    db.refresh(db_payment)
    
    # If status changed to paid, update the next billing date
    if old_status != "paid" and db_payment.status == "paid":
        update_next_billing_date(db, db_payment.subscription_id, user_id)
    
    return db_payment

def delete_payment(db: Session, payment_id: int, user_id: int) -> None:
    """
    Delete a payment
    """
    # Get the payment
    db_payment = get_payment_by_id(db, payment_id)
    if not db_payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # Check if subscription belongs to user
    subscription = get_subscription_by_id(db, db_payment.subscription_id, user_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Delete the payment
    db.delete(db_payment)
    db.commit()

def record_payment_for_subscription(
    db: Session, 
    subscription_id: int, 
    user_id: int,
    payment_date: Optional[date] = None,
    payment_method: Optional[str] = None,
    notes: Optional[str] = None
) -> PaymentHistory:
    """
    Automatically record a payment for a subscription
    """
    # Check if subscription exists and belongs to user
    subscription = get_subscription_by_id(db, subscription_id, user_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Use today's date if not provided
    if not payment_date:
        payment_date = date.today()
    
    # Create payment
    payment = PaymentCreate(
        subscription_id=subscription_id,
        payment_date=payment_date,
        amount=subscription.amount,
        status="paid",
        payment_method=payment_method or "Manual Entry",
        notes=notes
    )
    
    return create_payment(db, payment, user_id)