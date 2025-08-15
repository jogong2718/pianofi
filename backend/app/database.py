from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config_loader import Config

DATABASE_URL = Config.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=2,
    max_overflow=2,
    pool_timeout=5
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()