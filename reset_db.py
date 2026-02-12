import os
from app.database import engine, Base
from app import models  # Essential: This registers the models with SQLAlchemy

def reset_database():
    db_path = "event_system.db"
    
    # 1. Remove the old database file if it exists
    if os.path.exists(db_path):
        print(f"🗑️  Removing old database: {db_path}")
        os.remove(db_path)
    
    # 2. Use SQLAlchemy to create the tables from scratch
    try:
        print("🏗️  Creating fresh tables based on models...")
        Base.metadata.create_all(bind=engine)
        print("✨ Database recreated with professional logic!")
    except Exception as e:
        print(f"💥 Error creating database: {e}")

if __name__ == "__main__":
    reset_database()