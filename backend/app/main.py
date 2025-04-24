from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.api.routes import api_router
from app.db.database import get_db
from app.config import settings
import logging
import os

# Setup logging
logging.basicConfig(
    level=logging.getLevelName(settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Ensure log directory exists
log_dir = os.path.dirname(settings.LOG_FILE)
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Create file handler
file_handler = logging.FileHandler(settings.LOG_FILE)
file_handler.setLevel(logging.getLevelName(settings.LOG_LEVEL))
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

# Get root logger and add file handler
logger = logging.getLogger()
logger.addHandler(file_handler)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="API for subscription and billing management",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, you'd want to restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.APP_NAME} API"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    # Try to connect to the database
    try:
        # Execute a simple query
        db.execute("SELECT 1")
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=settings.APP_PORT, 
        reload=settings.APP_ENV == "development"
    )