from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional

from app.db.models import Category
from app.schemas.category import CategoryCreate, CategoryUpdate

def get_category_by_id(db: Session, category_id: int, user_id: int) -> Optional[Category]:
    """
    Get a category by ID for a specific user
    """
    return db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == user_id
    ).first()

def get_categories_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Category]:
    """
    Get categories for a user
    """
    return db.query(Category).filter(
        Category.user_id == user_id
    ).offset(skip).limit(limit).all()

def create_category(db: Session, category: CategoryCreate, user_id: int) -> Category:
    """
    Create a new category
    """
    # Create the category object
    db_category = Category(
        **category.dict(),
        user_id=user_id
    )
    
    # Add to database
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    return db_category

def update_category(db: Session, category_id: int, category: CategoryUpdate, user_id: int) -> Category:
    """
    Update an existing category
    """
    # Get the category
    db_category = get_category_by_id(db, category_id, user_id)
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Category not found"
        )
    
    # Update category fields
    update_data = category.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)
    
    # Commit changes
    db.commit()
    db.refresh(db_category)
    
    return db_category

def delete_category(db: Session, category_id: int, user_id: int) -> None:
    """
    Delete a category
    """
    # Get the category
    db_category = get_category_by_id(db, category_id, user_id)
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Category not found"
        )
    
    # Delete the category
    db.delete(db_category)
    db.commit()

def get_category_with_subscriptions_count(db: Session, user_id: int) -> List[dict]:
    """
    Get categories with their subscription counts
    """
    # This would use a join and group by in SQL
    # For simplicity, we'll do it in memory
    categories = get_categories_by_user(db, user_id)
    result = []
    
    for category in categories:
        subscription_count = len(category.subscriptions)
        cat_dict = {
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "color": category.color,
            "subscription_count": subscription_count
        }
        result.append(cat_dict)
    
    return result