"""
Database connection setup. It tells FastAPI 
how to talk to our database, where is it present, etc.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# creating a local sqlite database file
SQLALCHEMY_DATABASE_URL = "sqlite:///./event_system.db"

# core interface of the db is engine
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread":False}, echo=True)

# each instance of Sessionlocal will become database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# creating new db models by inheriting from Base class
Base = declarative_base()

# this is a dependency which ensures that a DB connection 
# starts (request initiated) and closes automatically (request finished)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()