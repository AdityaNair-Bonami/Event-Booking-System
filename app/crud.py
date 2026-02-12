"""
Create, Read, Update and Delete logic
"""

from sqlalchemy import extract, or_, func
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from datetime import datetime
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
    return db.query(models.Event).filter(models.Event.status == models.EventStatus.ACTIVE.value).order_by(models.Event.inventory_status.asc(), models.Event.date.asc()).offset(skip).limit(limit).all()

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
        if event_update.status == models.EventStatus.CANCELLED.value:
            bookings = db.query(models.Booking).join(models.Ticket).filter(models.Ticket.event_id == event_id).all()
            for b in bookings:
                b.status = models.BookingStatus.CANCELLED.value
        
        db.commit()
        db.refresh(db_event)
    return db_event

def delete_event(db: Session, event_id: int):
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if db_event:
        db.delete(db_event)
        db.commit()
    return db_event

def search_events(db: Session, location: str = None, is_weekend: bool = None, date: datetime = None, time_slot: str = None):
    # default active events first and sold out events later, all of these by date ascending
    query = db.query(models.Event).filter(models.Event.status == models.EventStatus.ACTIVE.value)

    # searching by venue
    if location and location.strip():
        query = query.filter(models.Event.venue.ilike(f"%{location}"))

    # searching by date 
    if date:
        query = query.filter(func.date(models.Event.date) == date.date())
    else:
        query = query.filter(models.Event.date >= datetime.now())
    
    # searching by time slot
    if time_slot:
        hour_col = func.strftime('%H', models.Event.date)
        ts = time_slot.lower().strip()
        if ts == "morning":
            query = query.filter(hour_col >= '06', hour_col < '12')
        elif ts in ["noon", "afternoon"]:
            query = query.filter(hour_col >= '12', hour_col < '17')
        elif ts == "evening":
            query = query.filter(hour_col >= '17', hour_col < '21')
        elif ts == "night":
            query = query.filter(or_(hour_col >= '21', hour_col < '06'))
    
    # weekend flag
    if is_weekend is not None:
        dow = dow = func.strftime('%w', models.Event.date)
        if is_weekend is True:
            # 0-6 with 0 as Sunday and 6 as Saturday
            query = query.filter(or_(dow == '0', dow == '6'))
        else:
            # 1-5 for weekdays
            query = query.filter(dow.in_(['1', '2', '3', '4', '5']))
    
    return query.order_by(models.Event.inventory_status.asc(), models.Event.date.asc()).all()

# booking logic for customers
def create_booking(db: Session, booking: schemas.BookingCreate, customer_id: int):
    # checking for ticket availability
    db_ticket = db.query(models.Ticket).filter(models.Ticket.id == booking.ticket_id).first()
    
    if not db_ticket:
        return None
    
    # converting the column value to python int for comparison
    if db_ticket.quantity_available < booking.quantity:
        return None

    # deducting stock
    db_ticket.quantity_available -= booking.quantity

    new_booking = models.Booking(
        customer_id = customer_id,
        ticket_id = booking.ticket_id,
        quantity = booking.quantity,
        status=models.BookingStatus.CONFIRMED.value
    )
    
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    db.refresh(db_ticket) # refreshing ticket to get updated quantity for inventory status calculation
    return new_booking

def get_user_bookings(db: Session, user_id: int):
    return db.query(models.Booking).filter(models.Booking.customer_id == user_id).all()

def get_event_bookings(db: Session, event_id:int):
    return db.query(models.Booking).join(models.Ticket).filter(models.Ticket.event_id == event_id).all()

def cancel_booking(db: Session, booking_id: int, user_id: int):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id, models.Booking.customer_id == user_id).first()
    
    if booking and booking.status != models.BookingStatus.CANCELLED.value:
        booking.status = models.BookingStatus.CANCELLED.value
        ticket = db.query(models.Ticket).filter(models.Ticket.id == booking.ticket_id).first()
        if ticket:
            ticket.quantity_available += booking.quantity # adding the cancelled quantity back to available stock

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