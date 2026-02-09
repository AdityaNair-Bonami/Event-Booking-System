"""
Entry point for the app. Initializes the database
and tells FastAPI which routes to use
"""

from typing import List, Any
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from . import models, schemas, database, auth, crud, tasks




# creating the database table
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Event Booking System")

@app.get("/")
def read_root():
    return {"message":"Welcome to the Event Booking API"}


# auth endpoints
@app.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pass = auth.get_password(user.password)
    new_user = models.User(email = user.email, hashed_password = hashed_pass, role = user.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/token")
def login_for_access_token(form_data: schemas.UserCreate, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.email).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = auth.create_access_token(data={"sub":user.email})
    return {"access_token": access_token,"token_type": "bearer"}


# event endpoit for organizer only
@app.post("/events", response_model=schemas.Event)
def create_new_event(
    event: schemas.EventCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.require_role("organizer"))
):
    user_id = int(getattr(current_user, 'id'))
    return crud.create_event(db=db, event=event, organizer_id=user_id)

@app.put("/events/{event_id}", response_model=schemas.Event)
def update_existing_event(
    event_id: int, 
    event_update: schemas.EventBase,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.require_role("organizer"))
):
    db_event = crud.update_event(db=db, event_id=event_id, event_update=event_update)
    if not db_event:
        return HTTPException(status_code=404, detail="Event not found!")
    # Celery notification task to be added here!
    emails = [booking.customer.email for ticket in db_event.tickets for booking in ticket.bookings]
    if emails:
        task_func: Any = tasks.notify_event_update
        task_func.delay(list(set(emails)), db_event.title)
    
    return db_event


# booking endpoints for customers only
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
    
    # Celery confirmation email task to be added here!
    confirm_task: Any = tasks.send_booking_confirmation
    confirm_task.delay(current_user.email, new_booking.ticket.event.title)
    
    return new_booking


# public endpoints
@app.get("/events/", response_model=List[schemas.Event])
def read_events(skip:int = 0, limit:int = 100, db:Session = Depends(database.get_db)):
    return crud.get_events(db, skip=skip, limit=limit)

