from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config_loader import Config
from sqlalchemy.pool import NullPool

DATABASE_URL = Config.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,           # don't hoard connections
    pool_pre_ping=True,
    connect_args={"sslmode": "require"},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()