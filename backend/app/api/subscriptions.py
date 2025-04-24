from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import date, datetime, timedelta

from app.db.database import get_db
from app.db.models import Subscription as SubscriptionModel, Category as CategoryModel
from app.schemas.subscription import (
    Subscription, 
    SubscriptionCreate, 
    SubscriptionUpdate, 
    SubscriptionWithCategory,
    SubscriptionSummary
)
# Dalam implementasi produksi, kita akan menambahkan autentikasi
# from app.auth.dependencies import get_current_user
# from app.db.models import User

router = APIRouter(
    prefix="/api/subscriptions",
    tags=["subscriptions"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=Subscription, status_code=201)
def create_subscription(
    subscription: SubscriptionCreate, 
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_user)
):
    """
    Membuat langganan baru.
    """
    # Untuk sementara, kita menggunakan user_id = 1 untuk testing
    # Dalam implementasi produksi, kita akan menggunakan user.id
    user_id = 1
    
    # Validasi category_id jika ada
    if subscription.category_id:
        category = db.query(CategoryModel).filter(
            CategoryModel.id == subscription.category_id,
            CategoryModel.user_id == user_id
        ).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    
    # Buat objek model langganan
    db_subscription = SubscriptionModel(
        **subscription.dict(),
        user_id=user_id
    )
    
    try:
        # Tambahkan dan commit ke database
        db.add(db_subscription)
        db.commit()
        db.refresh(db_subscription)
        return db_subscription
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Could not create subscription")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.get("/", response_model=List[SubscriptionWithCategory])
def get_subscriptions(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    sort_by: str = "next_billing_date",
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_user)
):
    """
    Mendapatkan daftar langganan pengguna dengan filter opsional.
    """
    # Untuk sementara, kita menggunakan user_id = 1 untuk testing
    user_id = 1
    
    # Memulai query dasar
    query = db.query(SubscriptionModel).filter(SubscriptionModel.user_id == user_id)
    
    # Terapkan filter
    if active_only:
        query = query.filter(SubscriptionModel.is_active == True)
    
    if category_id:
        query = query.filter(SubscriptionModel.category_id == category_id)
    
    if search:
        query = query.filter(SubscriptionModel.name.ilike(f"%{search}%"))
    
    # Terapkan pengurutan
    if sort_by == "name":
        query = query.order_by(SubscriptionModel.name)
    elif sort_by == "amount":
        query = query.order_by(SubscriptionModel.amount.desc())
    elif sort_by == "next_billing_date":
        query = query.order_by(SubscriptionModel.next_billing_date)
    elif sort_by == "created_at":
        query = query.order_by(SubscriptionModel.created_at.desc())
    
    # Terapkan pagination
    subscriptions = query.offset(skip).limit(limit).all()
    
    # Tambahkan informasi kategori ke respons
    result = []
    for sub in subscriptions:
        sub_dict = Subscription.from_orm(sub).dict()
        if sub.category:
            sub_dict["category"] = {
                "id": sub.category.id,
                "name": sub.category.name,
                "color": sub.category.color
            }
        result.append(SubscriptionWithCategory(**sub_dict))
    
    return result

@router.get("/summary", response_model=SubscriptionSummary)
def get_subscription_summary(
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_user)
):
    """
    Mendapatkan ringkasan langganan pengguna, termasuk total biaya bulanan dan tahunan,
    tagihan mendatang, dan pengelompokan berdasarkan kategori.
    """
    # Untuk sementara, kita menggunakan user_id = 1 untuk testing
    user_id = 1
    
    # Query langganan aktif
    active_subscriptions = db.query(SubscriptionModel).filter(
        SubscriptionModel.user_id == user_id,
        SubscriptionModel.is_active == True
    ).all()
    
    # Hitung total biaya bulanan dan tahunan
    monthly_total = 0
    yearly_total = 0
    
    # Buat dictionary untuk mengelompokkan berdasarkan kategori
    by_category = {}
    
    for sub in active_subscriptions:
        # Konversi biaya ke bulanan dan tahunan berdasarkan siklus penagihan
        monthly_amount = 0
        if sub.billing_cycle == "monthly":
            monthly_amount = sub.amount
        elif sub.billing_cycle == "quarterly":
            monthly_amount = sub.amount / 3
        elif sub.billing_cycle == "semiannual":
            monthly_amount = sub.amount / 6
        elif sub.billing_cycle == "annual":
            monthly_amount = sub.amount / 12
        
        yearly_amount = monthly_amount * 12
        
        monthly_total += monthly_amount
        yearly_total += yearly_amount
        
        # Kelompokkan berdasarkan kategori
        category_name = "Uncategorized"
        category_id = 0
        if sub.category:
            category_name = sub.category.name
            category_id = sub.category.id
        
        if category_id not in by_category:
            by_category[category_id] = {
                "id": category_id,
                "name": category_name,
                "color": sub.category.color if sub.category else "#808080",
                "count": 0,
                "monthly_amount": 0,
                "yearly_amount": 0
            }
        
        by_category[category_id]["count"] += 1
        by_category[category_id]["monthly_amount"] += monthly_amount
        by_category[category_id]["yearly_amount"] += yearly_amount
    
    # Ambil tagihan mendatang (30 hari ke depan)
    today = date.today()
    thirty_days_later = today + timedelta(days=30)
    
    upcoming_bills = db.query(SubscriptionModel).filter(
        SubscriptionModel.user_id == user_id,
        SubscriptionModel.is_active == True,
        SubscriptionModel.next_billing_date.between(today, thirty_days_later)
    ).order_by(SubscriptionModel.next_billing_date).limit(5).all()
    
    # Ambil langganan yang baru ditambahkan
    recently_added = db.query(SubscriptionModel).filter(
        SubscriptionModel.user_id == user_id
    ).order_by(SubscriptionModel.created_at.desc()).limit(5).all()
    
    return {
        "total_active": len(active_subscriptions),
        "total_amount_monthly": round(monthly_total, 2),
        "total_amount_yearly": round(yearly_total, 2),
        "upcoming_bills": upcoming_bills,
        "recently_added": recently_added,
        "by_category": by_category
    }

@router.get("/{subscription_id}", response_model=SubscriptionWithCategory)
def get_subscription(
    subscription_id: int = Path(..., title="The ID of the subscription to get"),
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_user)
):
    """
    Mendapatkan detail langganan berdasarkan ID.
    """
    # Untuk sementara, kita menggunakan user_id = 1 untuk testing
    user_id = 1
    
    subscription = db.query(SubscriptionModel).filter(
        SubscriptionModel.id == subscription_id,
        SubscriptionModel.user_id == user_id
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Tambahkan informasi kategori ke respons
    sub_dict = Subscription.from_orm(subscription).dict()
    if subscription.category:
        sub_dict["category"] = {
            "id": subscription.category.id,
            "name": subscription.category.name,
            "color": subscription.category.color
        }
    
    return SubscriptionWithCategory(**sub_dict)

@router.put("/{subscription_id}", response_model=Subscription)
def update_subscription(
    subscription_update: SubscriptionUpdate,
    subscription_id: int = Path(..., title="The ID of the subscription to update"),
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_user)
):
    """
    Memperbarui langganan berdasarkan ID.
    """
    # Untuk sementara, kita menggunakan user_id = 1 untuk testing
    user_id = 1
    
    # Cari langganan yang akan diperbarui
    subscription = db.query(SubscriptionModel).filter(
        SubscriptionModel.id == subscription_id,
        SubscriptionModel.user_id == user_id
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Validasi category_id jika ada
    if subscription_update.category_id is not None:
        if subscription_update.category_id > 0:
            category = db.query(CategoryModel).filter(
                CategoryModel.id == subscription_update.category_id,
                CategoryModel.user_id == user_id
            ).first()
            if not category:
                raise HTTPException(status_code=404, detail="Category not found")
    
    # Perbarui atribut yang ada di request
    update_data = subscription_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(subscription, key, value)
    
    try:
        db.commit()
        db.refresh(subscription)
        return subscription
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Could not update subscription")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.delete("/{subscription_id}", status_code=204)
def delete_subscription(
    subscription_id: int = Path(..., title="The ID of the subscription to delete"),
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_user)
):
    """
    Menghapus langganan berdasarkan ID.
    """
    # Untuk sementara, kita menggunakan user_id = 1 untuk testing
    user_id = 1
    
    # Cari langganan yang akan dihapus
    subscription = db.query(SubscriptionModel).filter(
        SubscriptionModel.id == subscription_id,
        SubscriptionModel.user_id == user_id
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    try:
        db.delete(subscription)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")