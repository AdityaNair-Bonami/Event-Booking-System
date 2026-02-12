import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import models, auth

def seed_data():
    db = SessionLocal()
    
    # 1. Organizer Credentials
    organizers_info = [
        {"email": "o1@test.com", "password": "o1"},
        {"email": "o2@test.com", "password": "o2"},
        {"email": "o3@test.com", "password": "o3"}
    ]
    
    organizer_map = {} # To store IDs: {orig_json_id: db_actual_id}

    print("🔑 Creating Organizers...")
    for i, info in enumerate(organizers_info, 1):
        # Check if user exists to avoid duplicates
        user = db.query(models.User).filter(models.User.email == info["email"]).first()
        if not user:
            hashed_pw = auth.get_password(info["password"])
            user = models.User(email=info["email"], hashed_password=hashed_pw, role="organizer")
            db.add(user)
            db.commit()
            db.refresh(user)
        organizer_map[i] = user.id
    
    # 2. Raw JSON Data from your Swagger
    events_json = """
    [
  {
    "title": "Retro Disco Night",
    "description": "Social & Nightlife",
    "date": "2026-03-02T22:00:00",
    "venue": "Pulse Nightclub",
    "id": 3,
    "organizer_id": 1,
    "status": "active",
    "inventory_status": "available",
    "tickets": [
      {
        "ticket_type": "Entry",
        "price": 50,
        "quantity_available": 200,
        "id": 3,
        "event_id": 3
      }
    ]
  },
  {
    "title": "Director's Cut: Sci-Fi Night",
    "description": "Entertainment",
    "date": "2026-03-05T20:30:00",
    "venue": "Grand Cinema Hall",
    "id": 9,
    "organizer_id": 2,
    "status": "active",
    "inventory_status": "available",
    "tickets": [
      {
        "ticket_type": "Standard",
        "price": 20,
        "quantity_available": 150,
        "id": 9,
        "event_id": 9
      }
    ]
  },
  {
    "title": "Indie Film Festival",
    "description": "Entertainment",
    "date": "2026-03-07T12:00:00",
    "venue": "Grand Cinema Hall",
    "id": 15,
    "organizer_id": 3,
    "status": "active",
    "inventory_status": "available",
    "tickets": [
      {
        "ticket_type": "Weekend Pass",
        "price": 35,
        "quantity_available": 100,
        "id": 15,
        "event_id": 15
      }
    ]
  },
  {
    "title": "Neon 5K Run",
    "description": "Active & Outdoors",
    "date": "2026-03-10T18:30:00",
    "venue": "The City Stadium",
    "id": 8,
    "organizer_id": 2,
    "status": "active",
    "inventory_status": "available",
    "tickets": [
      {
        "ticket_type": "Registration",
        "price": 25,
        "quantity_available": 300,
        "id": 8,
        "event_id": 8
      }
    ]
  },
  {
    "title": "Modern Art & Sculpture Expo",
    "description": "Intellectual & Expo",
    "date": "2026-03-12T11:00:00",
    "venue": "The Metro Convention Center",
    "id": 5,
    "organizer_id": 1,
    "status": "active",
    "inventory_status": "available",
    "tickets": [
      {
        "ticket_type": "Adult",
        "price": 30,
        "quantity_available": 300,
        "id": 5,
        "event_id": 5
      }
    ]
  },
  {
    "title": "Charity Soccer Match",
    "description": "Active & Outdoors",
    "date": "2026-03-12T13:00:00",
    "venue": "The City Stadium",
    "id": 14,
    "organizer_id": 3,
    "status": "active",
    "inventory_status": "available",
    "tickets": [
      {
        "ticket_type": "Supporter",
        "price": 20,
        "quantity_available": 1000,
        "id": 14,
        "event_id": 14
      }
    ]
  },
  {
    "title": "The Midnight Jazz Session",
    "description": "Social & Nightlife",
    "date": "2026-03-14T22:00:00",
    "venue": "Pulse Nightclub",
    "id": 4,
    "organizer_id": 1,
    "status": "active",
    "inventory_status": "available",
    "tickets": [
      {
        "ticket_type": "Table for 2",
        "price": 60,
        "quantity_available": 70,
        "id": 4,
        "event_id": 4
      }
    ]
  },
  {
    "title": "Masquerade Cocktail Gala",
    "description": "Social & Nightlife",
    "date": "2026-03-14T22:00:00",
    "venue": "Pulse Nightclub",
    "id": 12,
    "organizer_id": 2,
    "status": "active",
    "inventory_status": "available",
    "tickets": [
      {
        "ticket_type": "Open Bar",
        "price": 100,
        "quantity_available": 100,
        "id": 12,
        "event_id": 12
      }
    ]
  },
  {
    "title": "Gourmet Food & Wine Expo",
    "description": "Intellectual & Expo / Food & Drinks",
    "date": "2026-03-15T10:00:00",
    "venue": "The Metro Convention Center",
    "id": 16,
    "organizer_id": 3,
    "status": "active",
    "inventory_status": "available",
    "tickets": [
      {
        "ticket_type": "Weekend Pass",
        "price": 35,
        "quantity_available": 300,
        "id": 16,
        "event_id": 16
      }
    ]
  },
  {
    "title": "Corporate Tech Expo",
    "description": "Intellectual & Expo",
    "date": "2026-03-16T10:00:00",
    "venue": "The Metro Convention Center",
    "id": 13,
    "organizer_id": 3,
    "status": "active",
    "inventory_status": "available",
    "tickets": [
      {
        "ticket_type": "Visitor",
        "price": 200,
        "quantity_available": 500,
        "id": 13,
        "event_id": 13
      }
    ]
  },
  {
    "title": "Puppy Yoga & Brunch",
    "description": "Active & Outdoors, Pets",
    "date": "2026-03-20T10:30:00",
    "venue": "The City Stadium",
    "id": 10,
    "organizer_id": 2,
    "status": "active",
    "inventory_status": "available",
    "tickets": [
      {
        "ticket_type": "Human + Dog",
        "price": 35,
        "quantity_available": 40,
        "id": 10,
        "event_id": 10
      }
    ]
  },
  {
    "title": "The Stand-Up Gala",
    "description": "Stage & Performance",
    "date": "2026-03-20T19:00:00",
    "venue": "The Royal Theater",
    "id": 1,
    "organizer_id": 1,
    "status": "active",
    "inventory_status": "available",
    "tickets": [
      {
        "ticket_type": "VIP",
        "price": 50,
        "quantity_available": 50,
        "id": 1,
        "event_id": 1
      }
    ]
  },
  {
    "title": "Summer Solstice Music Fest",
    "description": "Stage & Performance / Fests & Fairs",
    "date": "2026-03-20T23:00:00",
    "venue": "The Royal Theater",
    "id": 11,
    "organizer_id": 2,
    "status": "active",
    "inventory_status": "available",
    "tickets": [
      {
        "ticket_type": "Weekend Pass",
        "price": 55,
        "quantity_available": 500,
        "id": 11,
        "event_id": 11
      }
    ]
  },
  {
    "title": "Improv Comedy Night",
    "description": "Intellectual & Expo",
    "date": "2026-03-21T21:00:00",
    "venue": "The Royal Theater",
    "id": 6,
    "organizer_id": 1,
    "status": "active",
    "inventory_status": "available",
    "tickets": [
      {
        "ticket_type": "Standard",
        "price": 30,
        "quantity_available": 90,
        "id": 6,
        "event_id": 6
      }
    ]
  },
  {
    "title": "Broadway Hits Live",
    "description": "Stage & Performance",
    "date": "2026-03-22T20:00:00",
    "venue": "The Royal Theater",
    "id": 7,
    "organizer_id": 2,
    "status": "active",
    "inventory_status": "available",
    "tickets": [
      {
        "ticket_type": "Orchestra",
        "price": 85,
        "quantity_available": 40,
        "id": 7,
        "event_id": 7
      }
    ]
  },
  {
    "title": "Open Air Cinema: Classic Horror",
    "description": "Entertainment",
    "date": "2026-03-22T20:00:00",
    "venue": "Grand Cinema Hall",
    "id": 17,
    "organizer_id": 3,
    "status": "active",
    "inventory_status": "available",
    "tickets": [
      {
        "ticket_type": "Recliner + Blanket + Snacks",
        "price": 20,
        "quantity_available": 80,
        "id": 17,
        "event_id": 17
      }
    ]
  },
  {
    "title": "Indian Super League Finals",
    "description": "Active & Outdoors",
    "date": "2026-03-22T20:00:00",
    "venue": "The City Stadium",
    "id": 18,
    "organizer_id": 3,
    "status": "active",
    "inventory_status": "available",
    "tickets": [
      {
        "ticket_type": "Supporter",
        "price": 40,
        "quantity_available": 1000,
        "id": 18,
        "event_id": 18
      }
    ]
  },
  {
    "title": "Deep Learning Symposium",
    "description": "Intellectual & Expo",
    "date": "2026-04-15T09:00:00",
    "venue": "The Metro Convention Center",
    "id": 2,
    "organizer_id": 1,
    "status": "active",
    "inventory_status": "available",
    "tickets": [
      {
        "ticket_type": "Full Pass",
        "price": 150,
        "quantity_available": 100,
        "id": 2,
        "event_id": 2
      }
    ]
  }
]
    """
    
    events_list = json.loads(events_json)
    
    print("📅 Seeding Events and Tickets...")
    for item in events_list:
        # Create Event
        new_event = models.Event(
            title=item["title"],
            description=item["description"],
            date=datetime.fromisoformat(item["date"]),
            venue=item["venue"],
            organizer_id=organizer_map[item["organizer_id"]],
            status=models.EventStatus.ACTIVE.value
        )
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        
        # Create Tickets for this Event
        for t in item["tickets"]:
            new_ticket = models.Ticket(
                ticket_type=t["ticket_type"],
                price=t["price"],
                quantity_available=t["quantity_available"],
                event_id=new_event.id
            )
            db.add(new_ticket)
    
    db.commit()
    db.close()
    print("✅ Database successfully seeded with 18 events!")

if __name__ == "__main__":
    seed_data()