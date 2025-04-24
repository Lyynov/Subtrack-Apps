from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Buat engine database berdasarkan konfigurasi
engine = create_engine(
    settings.DATABASE_URL, 
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

# Buat SessionLocal untuk membuat session database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class untuk model ORM
Base = declarative_base()

# Fungsi untuk mendapatkan koneksi database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()