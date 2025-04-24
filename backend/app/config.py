import os
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache

class Settings(BaseSettings):
    # Konfigurasi Aplikasi
    APP_NAME: str = "Subtrack"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_URL: str = "http://localhost:8000"
    APP_PORT: int = 8000
    
    # Konfigurasi Database
    DATABASE_URL: str = "sqlite:///./subtrack.db"
    
    # Keamanan
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Email Notifications
    MAIL_SERVER: Optional[str] = None
    MAIL_PORT: Optional[int] = None
    MAIL_USERNAME: Optional[str] = None
    MAIL_PASSWORD: Optional[str] = None
    MAIL_FROM: Optional[str] = None
    MAIL_TLS: bool = True
    MAIL_SSL: bool = False
    
    # Push Notifications
    PUSH_NOTIFICATION_KEY: Optional[str] = None
    
    # Email Parser
    IMAP_SERVER: Optional[str] = None
    IMAP_PORT: Optional[int] = None
    IMAP_USERNAME: Optional[str] = None
    IMAP_PASSWORD: Optional[str] = None
    IMAP_USE_SSL: bool = True
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/subtrack.log"
    
    # Timezone
    TIMEZONE: str = "Asia/Jakarta"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()