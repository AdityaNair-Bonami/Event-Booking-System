from app import models, database, auth
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

def seed():
    # Directly create a session from your project's engine
    db = database.SessionLocal()
    try:
        # Check if users exist to avoid duplicates
        if db.query(models.User).filter(models.User.email == "org@test.com").first():
            print("Database already seeded!")
            return

        print("Seeding data...")
        # 1. Create Organizer
        org_pass = auth.get_password("password123")
        organizer = models.User(email="org@test.com", hashed_password=org_pass, role="organizer")
        db.add(organizer)
        
        # 2. Create Customer
        cust_pass = auth.get_password("password123")
        customer = models.User(email="cust@test.com", hashed_password=cust_pass, role="customer")
        db.add(customer)
        db.flush() # This gets the IDs without committing yet

        # 3. Create Event
        event = models.Event(
            title="Alembic Masterclass",
            description="Learn database migrations like a pro.",
            date=datetime.now() + timedelta(days=5),
            venue="Virtual Hall A",
            organizer_id=organizer.id,
            status="active"
        )
        db.add(event)
        db.flush()

        # 4. Create Tickets
        ticket = models.Ticket(
            ticket_type="Standard", 
            price=49.99, 
            quantity_available=100, 
            event_id=event.id
        )
        db.add(ticket)
        
        db.commit()
        print("Done! Refresh Swagger and check GET /events/")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()