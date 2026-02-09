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
    return db.query(models.Event).offset(skip).limit(limit).all()


def update_event(db: Session, event_id: int, event_update: schemas.EventBase):
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if db_event:
        setattr(db_event, 'title', event_update.title)
        setattr(db_event, 'description', event_update.description)
        setattr(db_event, 'date', event_update.date)
        setattr(db_event, 'venue', event_update.venue)
        
        db.commit()
        db.refresh(db_event)
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
        quantity = booking.quantity
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    return new_booking


