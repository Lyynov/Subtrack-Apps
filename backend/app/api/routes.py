from fastapi import APIRouter

from app.api import subscriptions, users, notifications

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])