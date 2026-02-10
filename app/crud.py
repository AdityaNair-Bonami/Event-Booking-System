"""
Create, Read, Update and Delete logic
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Any
from . import models, schemas


# event management
def create_event(db: Session, event: schemas.EventCreate, organizer_id: int):
    # creating event object
    db_event = models.Event(
        title = event.title,
        description = event.description,
        date = event.date,
        venue = event.venue,
        organizer_id = organizer_id
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    # creating associated ticket types
    for ticket in event.tickets:
        db_ticket = models.Ticket(
            ticket_type = ticket.ticket_type,
            price = ticket.price,
            quantity_available = ticket.quantity_available,
            event_id = db_event.id
        )
        db.add(db_ticket)
    
    db.commit()
    db.refresh(db_event)
    return db_event


def get_events(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Event).filter(models.Event.status == "active").offset(skip).limit(limit).all()

def get_organizer_events(db: Session, organizer_id: int):
    return db.query(models.Event).filter(models.Event.organizer_id == organizer_id).all()

def update_event(db: Session, event_id: int, event_update: schemas.EventUpdate):
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if db_event:
        # updating only those fields which were requested
        update_data = event_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_event, key, value)
        # if an event is cancelled, cancel all associated bookings
        if event_update.status == "cancelled":
            bookings = db.query(models.Booking).join(models.Ticket).filter(models.Ticket.event_id == event_id).all()
            for b in bookings:
                setattr(b, "status", "cancelled")
        
        db.commit()
        db.refresh(db_event)
    return db_event

def delete_event(db: Session, event_id: int):
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if db_event:
        db.delete(db_event)
        db.commit()
    return db_event


# booking logic for customers
def create_booking(db: Session, booking: schemas.BookingCreate, customer_id: int):
    # checking for ticket availability
    db_ticket = db.query(models.Ticket).filter(models.Ticket.id == booking.ticket_id).first()
    
    if not db_ticket:
        return None
    
    # converting the column value to python int for comparison
    current_qty = getattr(db_ticket, 'quantity_available')
    if int(current_qty) < booking.quantity:
        return None

    # deducting stock
    setattr(db_ticket, 'quantity_available', current_qty - booking.quantity)

    new_booking = models.Booking(
        customer_id = customer_id,
        ticket_id = booking.ticket_id,
        quantity = booking.quantity,
        status="confirmed"
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    return new_booking

def get_user_bookings(db: Session, user_id: int):
    return db.query(models.Booking).filter(models.Booking.customer_id == user_id).all()

def get_event_bookings(db: Session, event_id:int):
    return db.query(models.Booking).join(models.Ticket).filter(models.Ticket.event_id == event_id).all()

def cancel_booking(db: Session, booking_id: int, user_id: int):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id, models.Booking.customer_id == user_id).first()
    if booking and str(booking.status) !="cancelled":
        setattr(booking, "status", "cancelled")
        ticket = db.query(models.Ticket).filter(models.Ticket.id == booking.ticket_id).first()
        if ticket:
            current_qty = getattr(ticket, "quantity_available")
            booked_qty = getattr(booking, "quantity")
            new_qty = current_qty + booked_qty
            setattr(ticket, "quantity_available", new_qty)
        db.commit()
        db.refresh(booking)
    return booking


# user management
def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        if user_update.email:
            setattr(db_user, "email", str(user_update.email))
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False