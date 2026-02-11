import sqlite3
import os

def reset_database():
    db_path = "event_system.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Disable foreign keys temporarily
        cursor.execute("PRAGMA foreign_keys = OFF;")

        # Get all table names (excluding internal sqlite tables and alembic migrations)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'alembic%';")
        tables = cursor.fetchall()

        for table in tables:
            table_name = table[0]
            print(f"🧹 Clearing table: {table_name}...")
            cursor.execute(f"DELETE FROM {table_name};")
            
            # Check if sqlite_sequence exists before trying to clear it
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence';")
            if cursor.fetchone():
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}';")

        conn.commit()
        cursor.execute("PRAGMA foreign_keys = ON;")
        conn.close()
        print("\n✨ Database is now sparkling clean! Ready for the demo.")

    except Exception as e:
        print(f"💥 Error resetting database: {e}")

if __name__ == "__main__":
    reset_database()