from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import date, datetime

from app.db.database import get_db
from app.services.reporting_service import (
    get_monthly_report,
    get_yearly_report,
    get_payment_history_report,
    get_subscription_trend_report
)

# In a production implementation, we would use authentication
# from app.auth.dependencies import get_current_user
# from app.db.models import User

router = APIRouter()

@router.get("/monthly/{year}/{month}")
def read_monthly_report(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_user)
):
    """
    Get monthly subscription report.
    """
    # For now, we'll use user_id = 1 for testing
    user_id = 1
    
    # Validate month
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Month must be between 1 and 12"
        )
    
    return get_monthly_report(db, user_id=user_id, year=year, month=month)

@router.get("/yearly/{year}")
def read_yearly_report(
    year: int,
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_user)
):
    """
    Get yearly subscription report.
    """
    # For now, we'll use user_id = 1 for testing
    user_id = 1
    
    return get_yearly_report(db, user_id=user_id, year=year)

@router.get("/payments")
def read_payment_history(
    start_date: date,
    end_date: date,
    subscription_id: Optional[int] = None,
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_user)
):
    """
    Get payment history for a date range.
    """
    # For now, we'll use user_id = 1 for testing
    user_id = 1
    
    # Validate date range
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date"
        )
    
    return get_payment_history_report(
        db, 
        user_id=user_id, 
        start_date=start_date, 
        end_date=end_date,
        subscription_id=subscription_id
    )

@router.get("/trends")
def read_subscription_trends(
    months: int = Query(12, ge=1, le=60),
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_user)
):
    """
    Get subscription trends over time.
    """
    # For now, we'll use user_id = 1 for testing
    user_id = 1
    
    return get_subscription_trend_report(db, user_id=user_id, months=months)

@router.get("/export/monthly/{year}/{month}")
def export_monthly_report(
    year: int,
    month: int,
    format: str = Query("pdf", regex="^(pdf|excel)$"),
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_user)
):
    """
    Export monthly report as PDF or Excel.
    """
    # For now, we'll use user_id = 1 for testing
    user_id = 1
    
    # Validate month
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Month must be between 1 and 12"
        )
    
    # This is a placeholder for the actual export implementation
    # In a real implementation, we would generate PDF or Excel file
    # For now, just return a message
    return {
        "message": f"Export of {format} report for {year}-{month:02d} will be implemented in the future."
    }

@router.get("/export/yearly/{year}")
def export_yearly_report(
    year: int,
    format: str = Query("pdf", regex="^(pdf|excel)$"),
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_user)
):
    """
    Export yearly report as PDF or Excel.
    """
    # For now, we'll use user_id = 1 for testing
    user_id = 1
    
    # This is a placeholder for the actual export implementation
    # In a real implementation, we would generate PDF or Excel file
    # For now, just return a message
    return {
        "message": f"Export of {format} report for {year} will be implemented in the future."
    }