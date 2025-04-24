from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.db.models import Category as CategoryModel
from app.schemas.category import Category, CategoryCreate, CategoryUpdate
from app.services.category_service import (
    create_category,
    get_categories_by_user,
    get_category_by_id,
    update_category,
    delete_category,
    get_category_with_subscriptions_count
)

# In a production implementation, we would use authentication
# from app.auth.dependencies import get_current_user
# from app.db.models import User

router = APIRouter()

@router.post("/", response_model=Category, status_code=status.HTTP_201_CREATED)
def create_new_category(
    category: CategoryCreate, 
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_user)
):
    """
    Create a new category.
    """
    # For now, we'll use user_id = 1 for testing
    # In a production implementation, we would use user.id
    user_id = 1
    
    return create_category(db=db, category=category, user_id=user_id)

@router.get("/", response_model=List[Category])
def read_categories(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_user)
):
    """
    Retrieve categories for a user.
    """
    # For now, we'll use user_id = 1 for testing
    user_id = 1
    
    categories = get_categories_by_user(db, user_id=user_id, skip=skip, limit=limit)
    return categories

@router.get("/with-count", response_model=List[dict])
def read_categories_with_count(
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_user)
):
    """
    Retrieve categories with subscription counts.
    """
    # For now, we'll use user_id = 1 for testing
    user_id = 1
    
    return get_category_with_subscriptions_count(db, user_id=user_id)

@router.get("/{category_id}", response_model=Category)
def read_category(
    category_id: int = Path(..., title="The ID of the category to get"),
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_user)
):
    """
    Get a specific category by id.
    """
    # For now, we'll use user_id = 1 for testing
    user_id = 1
    
    category = get_category_by_id(db, category_id=category_id, user_id=user_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Category not found"
        )
    return category

@router.put("/{category_id}", response_model=Category)
def update_category_info(
    category_id: int,
    category: CategoryUpdate,
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_user)
):
    """
    Update a category.
    """
    # For now, we'll use user_id = 1 for testing
    user_id = 1
    
    return update_category(db=db, category_id=category_id, category=category, user_id=user_id)

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category_by_id(
    category_id: int,
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_user)
):
    """
    Delete a category.
    """
    # For now, we'll use user_id = 1 for testing
    user_id = 1
    
    delete_category(db=db, category_id=category_id, user_id=user_id)
    return None