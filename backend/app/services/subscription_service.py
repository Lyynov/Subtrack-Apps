from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta

from app.db.models import Subscription, Category, User, BillingCycle
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate

def get_subscription_by_id(db: Session, subscription_id: int, user_id: int) -> Optional[Subscription]:
    """
    Get a subscription by ID for a specific user
    """
    return db.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == user_id
    ).first()

def get_subscriptions(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100,
    active_only: bool = False,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    sort_by: str = "next_billing_date"
) -> List[Subscription]:
    """
    Get multiple subscriptions for a user with optional filters
    """
    # Base query
    query = db.query(Subscription).filter(Subscription.user_id == user_id)
    
    # Apply filters
    if active_only:
        query = query.filter(Subscription.is_active == True)
    
    if category_id:
        query = query.filter(Subscription.category_id == category_id)
    
    if search:
        query = query.filter(Subscription.name.ilike(f"%{search}%"))
    
    # Apply sorting
    if sort_by == "name":
        query = query.order_by(Subscription.name)
    elif sort_by == "amount":
        query = query.order_by(Subscription.amount.desc())
    elif sort_by == "next_billing_date":
        query = query.order_by(Subscription.next_billing_date)
    elif sort_by == "created_at":
        query = query.order_by(Subscription.created_at.desc())
    
    # Apply pagination
    return query.offset(skip).limit(limit).all()

def create_subscription(db: Session, subscription: SubscriptionCreate, user_id: int) -> Subscription:
    """
    Create a new subscription
    """
    # Check if category exists if specified
    if subscription.category_id:
        category = db.query(Category).filter(
            Category.id == subscription.category_id,
            Category.user_id == user_id
        ).first()
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
    
    # Create the subscription object
    db_subscription = Subscription(
        **subscription.dict(),
        user_id=user_id
    )
    
    # Add to database
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)
    
    return db_subscription

def update_subscription(
    db: Session, 
    subscription_id: int, 
    subscription: SubscriptionUpdate, 
    user_id: int
) -> Subscription:
    """
    Update an existing subscription
    """
    # Get the subscription
    db_subscription = get_subscription_by_id(db, subscription_id, user_id)
    if not db_subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Subscription not found"
        )
    
    # Check if category exists if specified
    if subscription.category_id is not None:
        if subscription.category_id > 0:
            category = db.query(Category).filter(
                Category.id == subscription.category_id,
                Category.user_id == user_id
            ).first()
            
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found"
                )
    
    # Update subscription fields
    update_data = subscription.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_subscription, key, value)
    
    # Commit changes
    db.commit()
    db.refresh(db_subscription)
    
    return db_subscription

def delete_subscription(db: Session, subscription_id: int, user_id: int) -> None:
    """
    Delete a subscription
    """
    # Get the subscription
    db_subscription = get_subscription_by_id(db, subscription_id, user_id)
    if not db_subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Subscription not found"
        )
    
    # Delete the subscription
    db.delete(db_subscription)
    db.commit()

def get_monthly_subscription_amount(subscription: Subscription) -> float:
    """
    Calculate the monthly amount of a subscription based on its billing cycle
    """
    if subscription.billing_cycle == BillingCycle.MONTHLY:
        return subscription.amount
    elif subscription.billing_cycle == BillingCycle.QUARTERLY:
        return subscription.amount / 3
    elif subscription.billing_cycle == BillingCycle.SEMIANNUAL:
        return subscription.amount / 6
    elif subscription.billing_cycle == BillingCycle.ANNUAL:
        return subscription.amount / 12
    else:  # Custom
        # For custom cycles, we might need additional logic
        return subscription.amount / 30  # Assuming 30 days as a default

def get_subscription_summary(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Get a summary of subscriptions for a user, including total costs and categorization
    """
    # Get active subscriptions
    active_subscriptions = db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.is_active == True
    ).all()
    
    # Calculate totals
    monthly_total = 0
    yearly_total = 0
    by_category = {}
    
    for sub in active_subscriptions:
        # Calculate monthly amount
        monthly_amount = get_monthly_subscription_amount(sub)
        yearly_amount = monthly_amount * 12
        
        monthly_total += monthly_amount
        yearly_total += yearly_amount
        
        # Group by category
        category_name = "Uncategorized"
        category_id = 0
        category_color = "#808080"
        
        if sub.category:
            category_name = sub.category.name
            category_id = sub.category.id
            category_color = sub.category.color
        
        if category_id not in by_category:
            by_category[category_id] = {
                "id": category_id,
                "name": category_name,
                "color": category_color,
                "count": 0,
                "monthly_amount": 0,
                "yearly_amount": 0
            }
        
        by_category[category_id]["count"] += 1
        by_category[category_id]["monthly_amount"] += monthly_amount
        by_category[category_id]["yearly_amount"] += yearly_amount
    
    # Get upcoming bills (next 30 days)
    today = date.today()
    thirty_days_later = today + timedelta(days=30)
    
    upcoming_bills = db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.is_active == True,
        Subscription.next_billing_date.between(today, thirty_days_later)
    ).order_by(Subscription.next_billing_date).limit(5).all()
    
    # Get recently added subscriptions
    recently_added = db.query(Subscription).filter(
        Subscription.user_id == user_id
    ).order_by(Subscription.created_at.desc()).limit(5).all()
    
    # Return the summary
    return {
        "total_active": len(active_subscriptions),
        "total_amount_monthly": round(monthly_total, 2),
        "total_amount_yearly": round(yearly_total, 2),
        "upcoming_bills": upcoming_bills,
        "recently_added": recently_added,
        "by_category": by_category
    }

def get_subscriptions_due_soon(
    db: Session, 
    days_ahead: int = 7
) -> List[Subscription]:
    """
    Get subscriptions that are due in the next X days
    for notification purposes
    """
    today = date.today()
    future_date = today + timedelta(days=days_ahead)
    
    return db.query(Subscription).filter(
        Subscription.is_active == True,
        Subscription.next_billing_date.between(today, future_date)
    ).all()

def update_next_billing_date(
    db: Session, 
    subscription_id: int,
    user_id: int
) -> Subscription:
    """
    Update the next billing date after a payment is made
    """
    # Get the subscription
    db_subscription = get_subscription_by_id(db, subscription_id, user_id)
    if not db_subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Subscription not found"
        )
    
    # Calculate the next billing date based on billing cycle
    current_date = db_subscription.next_billing_date
    
    if db_subscription.billing_cycle == BillingCycle.MONTHLY:
        # Add one month, but keep the same day of month
        next_month = current_date.month + 1
        next_year = current_date.year
        
        if next_month > 12:
            next_month = 1
            next_year += 1
        
        # Handle day of month issues (e.g., Jan 31 -> Feb 28)
        try:
            next_date = date(next_year, next_month, current_date.day)
        except ValueError:
            # If the day doesn't exist in the next month, use the last day
            next_date = date(next_year, next_month, 1) + timedelta(days=32)
            next_date = next_date.replace(day=1) - timedelta(days=1)
    
    elif db_subscription.billing_cycle == BillingCycle.QUARTERLY:
        # Add three months
        next_month = current_date.month + 3
        next_year = current_date.year
        
        if next_month > 12:
            next_month = next_month - 12
            next_year += 1
        
        # Handle day of month issues
        try:
            next_date = date(next_year, next_month, current_date.day)
        except ValueError:
            next_date = date(next_year, next_month, 1) + timedelta(days=32)
            next_date = next_date.replace(day=1) - timedelta(days=1)
    
    elif db_subscription.billing_cycle == BillingCycle.SEMIANNUAL:
        # Add six months
        next_month = current_date.month + 6
        next_year = current_date.year
        
        if next_month > 12:
            next_month = next_month - 12
            next_year += 1
        
        # Handle day of month issues
        try:
            next_date = date(next_year, next_month, current_date.day)
        except ValueError:
            next_date = date(next_year, next_month, 1) + timedelta(days=32)
            next_date = next_date.replace(day=1) - timedelta(days=1)
    
    elif db_subscription.billing_cycle == BillingCycle.ANNUAL:
        # Add one year
        next_date = date(current_date.year + 1, current_date.month, current_date.day)
    
    else:  # Custom - for custom we'd need more info, defaulting to +30 days
        next_date = current_date + timedelta(days=30)
    
    # Update the subscription
    db_subscription.next_billing_date = next_date
    db.commit()
    db.refresh(db_subscription)
    
    return db_subscription