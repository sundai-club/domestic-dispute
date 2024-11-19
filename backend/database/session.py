from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Create SQLite database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./disputes.db"

# Create database engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()

def init_db():
    # Import models here to avoid circular imports
    from .models import Dispute
    Base.metadata.create_all(bind=engine)
