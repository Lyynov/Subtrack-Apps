from sqlalchemy.orm import Session
from sqlalchemy import func, extract, cast, Date
from typing import Dict, List, Optional, Any
from datetime import date, datetime, timedelta
import calendar

from app.db.models import Subscription, Category, PaymentHistory
from app.services.subscription_service import get_monthly_subscription_amount

def get_monthly_report(db: Session, user_id: int, year: int, month: int) -> Dict[str, Any]:
    """
    Generate a monthly subscription report
    """
    # Get all active subscriptions for the user
    subscriptions = db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.is_active == True
    ).all()
    
    # Initialize report data
    total_amount = 0
    by_category = {}
    subscription_details = []
    
    # Calculate month days range
    _, last_day = calendar.monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)
    
    # Process each subscription
    for sub in subscriptions:
        # Calculate the monthly cost
        monthly_amount = get_monthly_subscription_amount(sub)
        
        # Check if this subscription is billed in this month
        is_billed_this_month = False
        billing_date = None
        
        # For monthly subscriptions, check if billing day is in this month
        if sub.billing_cycle == "monthly":
            # Handle edge cases where billing day is greater than days in month
            actual_billing_day = min(sub.billing_day, last_day)
            billing_date = date(year, month, actual_billing_day)
            is_billed_this_month = True
        
        # For quarterly subscriptions
        elif sub.billing_cycle == "quarterly":
            next_billing = sub.next_billing_date
            if start_date <= next_billing <= end_date:
                billing_date = next_billing
                is_billed_this_month = True
        
        # For semiannual subscriptions
        elif sub.billing_cycle == "semiannual":
            next_billing = sub.next_billing_date
            if start_date <= next_billing <= end_date:
                billing_date = next_billing
                is_billed_this_month = True
        
        # For annual subscriptions
        elif sub.billing_cycle == "annual":
            next_billing = sub.next_billing_date
            if start_date <= next_billing <= end_date:
                billing_date = next_billing
                is_billed_this_month = True
        
        # Add to the total if billed this month
        if is_billed_this_month:
            total_amount += sub.amount  # This is the actual billing amount (not monthly equivalent)
        
        # Always add to the monthly total for reporting
        total_monthly_equivalent = monthly_amount
        
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
                "amount": 0,
                "monthly_equivalent": 0
            }
        
        by_category[category_id]["count"] += 1
        if is_billed_this_month:
            by_category[category_id]["amount"] += sub.amount
        by_category[category_id]["monthly_equivalent"] += monthly_amount
        
        # Add subscription details
        subscription_details.append({
            "id": sub.id,
            "name": sub.name,
            "billing_cycle": sub.billing_cycle,
            "amount": sub.amount,
            "monthly_equivalent": monthly_amount,
            "next_billing_date": sub.next_billing_date.isoformat(),
            "is_billed_this_month": is_billed_this_month,
            "billing_date": billing_date.isoformat() if billing_date else None,
            "category": {
                "id": category_id,
                "name": category_name,
                "color": category_color
            }
        })
    
    # Get actual payment history for this month
    payments = db.query(PaymentHistory).filter(
        PaymentHistory.payment_date.between(start_date, end_date),
        PaymentHistory.subscription_id.in_([sub.id for sub in subscriptions])
    ).all()
    
    payment_history = []
    for payment in payments:
        subscription = next((sub for sub in subscriptions if sub.id == payment.subscription_id), None)
        if subscription:
            payment_history.append({
                "id": payment.id,
                "subscription_id": payment.subscription_id,
                "subscription_name": subscription.name,
                "payment_date": payment.payment_date.isoformat(),
                "amount": payment.amount,
                "status": payment.status,
                "payment_method": payment.payment_method,
                "notes": payment.notes
            })
    
    # Calculate total monthly equivalent for all subscriptions
    total_monthly_equivalent = sum(get_monthly_subscription_amount(sub) for sub in subscriptions)
    
    return {
        "year": year,
        "month": month,
        "total_billed_amount": round(total_amount, 2),
        "total_monthly_equivalent": round(total_monthly_equivalent, 2),
        "subscription_count": len(subscriptions),
        "by_category": list(by_category.values()),
        "subscription_details": subscription_details,
        "payment_history": payment_history
    }

def get_yearly_report(db: Session, user_id: int, year: int) -> Dict[str, Any]:
    """
    Generate a yearly subscription report
    """
    # Initialize monthly data
    monthly_data = []
    total_yearly_amount = 0
    
    # Generate monthly reports for each month
    for month in range(1, 13):
        monthly_report = get_monthly_report(db, user_id, year, month)
        monthly_data.append({
            "month": month,
            "month_name": calendar.month_name[month],
            "total_billed_amount": monthly_report["total_billed_amount"],
            "total_monthly_equivalent": monthly_report["total_monthly_equivalent"],
            "subscription_count": monthly_report["subscription_count"]
        })
        total_yearly_amount += monthly_report["total_billed_amount"]
    
    # Get all active subscriptions for the user
    subscriptions = db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.is_active == True
    ).all()
    
    # Calculate total annual equivalent
    total_annual_equivalent = sum(get_monthly_subscription_amount(sub) * 12 for sub in subscriptions)
    
    # Group by category
    by_category = {}
    for sub in subscriptions:
        monthly_amount = get_monthly_subscription_amount(sub)
        annual_amount = monthly_amount * 12
        
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
                "annual_amount": 0
            }
        
        by_category[category_id]["count"] += 1
        by_category[category_id]["annual_amount"] += annual_amount
    
    return {
        "year": year,
        "total_yearly_amount": round(total_yearly_amount, 2),
        "total_annual_equivalent": round(total_annual_equivalent, 2),
        "subscription_count": len(subscriptions),
        "monthly_data": monthly_data,
        "by_category": list(by_category.values())
    }

def get_payment_history_report(
    db: Session, 
    user_id: int, 
    start_date: date, 
    end_date: date,
    subscription_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get payment history report for a date range
    """
    # Base query
    query = db.query(PaymentHistory).join(
        Subscription, PaymentHistory.subscription_id == Subscription.id
    ).filter(
        Subscription.user_id == user_id,
        PaymentHistory.payment_date.between(start_date, end_date)
    )
    
    # Filter by subscription if provided
    if subscription_id:
        query = query.filter(PaymentHistory.subscription_id == subscription_id)
    
    # Get payments
    payments = query.order_by(PaymentHistory.payment_date.desc()).all()
    
    # Format results
    result = []
    for payment in payments:
        subscription = db.query(Subscription).filter(Subscription.id == payment.subscription_id).first()
        if subscription:
            result.append({
                "id": payment.id,
                "subscription_id": payment.subscription_id,
                "subscription_name": subscription.name,
                "payment_date": payment.payment_date.isoformat(),
                "amount": payment.amount,
                "status": payment.status,
                "payment_method": payment.payment_method,
                "notes": payment.notes,
                "category": {
                    "id": subscription.category.id if subscription.category else 0,
                    "name": subscription.category.name if subscription.category else "Uncategorized",
                    "color": subscription.category.color if subscription.category else "#808080"
                }
            })
    
    return result

def get_subscription_trend_report(db: Session, user_id: int, months: int = 12) -> Dict[str, Any]:
    """
    Get subscription trends over time
    """
    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=30 * months)
    
    # Get all subscriptions that were created in the period
    subscriptions = db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.created_at >= start_date
    ).order_by(Subscription.created_at).all()
    
    # Format monthly data
    monthly_data = []
    current_date = start_date.replace(day=1)
    end_of_month = end_date.replace(day=1)
    
    while current_date <= end_of_month:
        year = current_date.year
        month = current_date.month
        month_end = date(year, month, calendar.monthrange(year, month)[1])
        
        # Count subscriptions
        active_count = 0
        total_monthly = 0
        new_subscriptions = 0
        
        for sub in subscriptions:
            # Check if subscription was active in this month
            created_date = sub.created_at.date()
            
            # New subscriptions this month
            if created_date.year == year and created_date.month == month:
                new_subscriptions += 1
            
            # Active in this month
            if created_date <= month_end:
                is_active = True
                if sub.end_date and sub.end_date <= month_end:
                    is_active = False
                
                if is_active:
                    active_count += 1
                    total_monthly += get_monthly_subscription_amount(sub)
        
        monthly_data.append({
            "year": year,
            "month": month,
            "month_name": calendar.month_name[month],
            "active_count": active_count,
            "total_monthly": round(total_monthly, 2),
            "new_subscriptions": new_subscriptions
        })
        
        # Move to next month
        if month == 12:
            current_date = date(year + 1, 1, 1)
        else:
            current_date = date(year, month + 1, 1)
    
    return {
        "trend_period_months": months,
        "monthly_data": monthly_data
    }