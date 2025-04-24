from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.db.database import get_db
from app.schemas.payment import Payment, PaymentCreate, PaymentUpdate, PaymentWithSubscription
from app.services.payment_service import (
    create_payment,
    get_payments_by_subscription,
    get_payments_by_user,
    get_payment_by_id,
    update_payment,
    delete_payment,
    record_payment_for_subscription
)

# In a production implementation, we would use authentication
# from app.auth.dependencies import get_current_user
# from app.db.models import User

router = APIRouter()

@router.post("/", response_model=Payment, status_code=status.HTTP_201_CREATED)
def create_new_payment(
    payment: PaymentCreate, 
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_user)
):
    """
    Create a new payment record.
    """
    # For now, we'll use user_id = 1 for testing
    user_id = 1
    
    return create_payment(db=db, payment=payment, user_id=user_id)

@router.get("/", response_model=List[PaymentWithSubscription])
def read_payments(
    skip: int = 0, 
    limit: int = 100,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_user)
):
    """
    Retrieve payments for a user with optional filters.
    """
    # For now, we'll use user_id = 1 for testing
    user_id = 1
    
    payments = get_payments_by_user(
        db, 
        user_id=user_id, 
        skip=skip, 
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        status=status
    )
    
    # Format the response with subscription details
    result = []
    for payment in payments:
        subscription = payment.subscription
        p_dict = {
            "id": payment.id,
            "subscription_id": payment.subscription_id,
            "payment_date": payment.payment_date,
            "amount": payment.amount,
            "status": payment.status,
            "payment_method": payment.payment_method,
            "receipt_url": payment.receipt_url,
            "notes": payment.notes,
            "created_at": payment.created_at,
            "subscription_name": subscription.name,
            "category_name": subscription.category.name if subscription.category else None,
            "category_color": subscription.category.color if subscription.category else None
        }
        result.append(PaymentWithSubscription(**p_dict))
    
    return result

@router.get("/subscription/{subscription_id}", response_model=List[Payment])
def read_payments_by_subscription(
    subscription_id: int = Path(..., title="The ID of the subscription to get payments for"),
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_user)
):
    """
    Retrieve payments for a specific subscription.
    """
    # For now, we'll use user_id = 1 for testing
    user_id = 1
    
    return get_payments_by_subscription(
        db, 
        subscription_id=subscription_id, 
        user_id=user_id,
        skip=skip, 
        limit=limit
    )

@router.get("/{payment_id}", response_model=Payment)
def read_payment(
    payment_id: int = Path(..., title="The ID of the payment to get"),
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_user)
):
    """
    Get a specific payment by id.
    """
    # For now, we'll use user_id = 1 for testing
    user_id = 1
    
    payment = get_payment_by_id(db, payment_id=payment_id)
    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Payment not found"
        )
    
    # Check if the payment belongs to a subscription owned by this user
    subscription = payment.subscription
    if subscription.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Payment not found"
        )
    
    return payment

@router.put("/{payment_id}", response_model=Payment)
def update_payment_info(
    payment_id: int,
    payment: PaymentUpdate,
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_user)
):
    """
    Update a payment.
    """
    # For now, we'll use user_id = 1 for testing
    user_id = 1
    
    return update_payment(db=db, payment_id=payment_id, payment=payment, user_id=user_id)

@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_by_id(
    payment_id: int,
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_user)
):
    """
    Delete a payment.
    """
    # For now, we'll use user_id = 1 for testing
    user_id = 1
    
    delete_payment(db=db, payment_id=payment_id, user_id=user_id)
    return None

@router.post("/record/{subscription_id}", response_model=Payment)
def record_payment(
    subscription_id: int,
    payment_date: Optional[date] = None,
    payment_method: Optional[str] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_user)
):
    """
    Record a payment for a subscription.
    """
    # For now, we'll use user_id = 1 for testing
    user_id = 1
    
    return record_payment_for_subscription(
        db, 
        subscription_id=subscription_id, 
        user_id=user_id,
        payment_date=payment_date,
        payment_method=payment_method,
        notes=notes
    )