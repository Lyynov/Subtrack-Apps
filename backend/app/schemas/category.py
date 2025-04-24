from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: str = "#1E90FF"  # Default color - dodgerblue

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None

class Category(CategoryBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        orm_mode = True