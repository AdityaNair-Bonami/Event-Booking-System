"""
Entry point for the app. Initializes the database
and tells FastAPI which routes to use
"""

from typing import List, Any
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from . import models, schemas, database, auth, crud, tasks

app = FastAPI(title="Event Booking System")

# --- ROOT & AUTH ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the Event Booking API"}

@app.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pass = auth.get_password(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_pass, role=user.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/token")
def login_for_access_token(form_data: schemas.UserCreate, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.email).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# --- ORGANIZER ENDPOINTS ---

@app.post("/events", response_model=schemas.Event)
def create_new_event(
    event: schemas.EventCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.require_role("organizer"))
):
    user_id = int(getattr(current_user, 'id'))
    return crud.create_event(db=db, event=event, organizer_id=user_id)

@app.get("/organizer/events", response_model=List[schemas.Event])
def list_organizer_events(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.require_role("organizer"))
):
    user_id = int(getattr(current_user, 'id'))
    return crud.get_organizer_events(db, user_id)

@app.put("/events/{event_id}", response_model=schemas.Event)
def update_existing_event(
    event_id: int, 
    event_update: schemas.EventUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.require_role("organizer"))
):
    db_event = crud.update_event(db=db, event_id=event_id, event_update=event_update)
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found!")

    # If event was updated or cancelled, notify customers via Celery
    emails = [b.customer.email for t in db_event.tickets for b in t.bookings if str(b.status) == "confirmed"]
    if emails:
        task_func: Any = tasks.notify_event_update
        msg = f"Update for {db_event.title}" if str(db_event.status) == "active" else f"CANCELLED: {db_event.title}"
        task_func.delay(list(set(emails)), msg)
    
    return db_event

@app.delete("/events/{event_id}")
def delete_event(
    event_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.require_role("organizer"))
):
    success = crud.delete_event(db, event_id)
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"message": "Event permanently deleted"}

# --- CUSTOMER ENDPOINTS ---

@app.get("/events/", response_model=List[schemas.Event])
def read_public_events(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    return crud.get_events(db, skip=skip, limit=limit)

@app.post("/bookings/", response_model=schemas.Booking)
def book_event_ticket(
    booking: schemas.BookingCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.require_role("customer"))
):
    user_id = int(getattr(current_user, 'id'))
    new_booking = crud.create_booking(db=db, booking=booking, customer_id=user_id)
    if not new_booking:
        raise HTTPException(status_code=400, detail="Tickets unavailable or insufficient")
    
    confirm_task: Any = tasks.send_booking_confirmation
    confirm_task.delay(current_user.email, f"Confirmed: {new_booking.ticket.event.title}")
    return new_booking

@app.get("/bookings/my", response_model=List[schemas.Booking])
def get_my_bookings(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.require_role("customer"))
):
    user_id = int(getattr(current_user, 'id'))
    return crud.get_user_bookings(db, user_id)

@app.put("/bookings/{booking_id}/cancel", response_model=schemas.Booking)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.require_role("customer"))
):
    user_id = int(getattr(current_user, 'id'))
    booking = crud.cancel_booking(db, booking_id, user_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found or already cancelled")
    
    confirm_task: Any = tasks.send_booking_confirmation
    confirm_task.delay(current_user.email, f"CANCELLED: {booking.ticket.event.title}")
    return booking

# --- PROFILE MANAGEMENT (BOTH ROLES) ---

@app.put("/users/me", response_model=schemas.User)
def update_my_profile(
    user_update: schemas.UserUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    user_id = int(getattr(current_user, 'id'))
    return crud.update_user(db, user_id, user_update)

@app.delete("/users/me")
def delete_my_profile(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    user_id = int(getattr(current_user, 'id'))
    crud.delete_user(db, user_id)
    return {"message": "Profile and all associated data deleted"}