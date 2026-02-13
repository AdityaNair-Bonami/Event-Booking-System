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
    return db.query(models.Event).filter(models.Event.status == models.EventStatus.ACTIVE.value, models.Event.deleted_at == None).order_by(models.Event.inventory_status.asc(), models.Event.date.asc()).offset(skip).limit(limit).all()

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
        db_event.deleted_at = datetime.now() # soft delete by setting deleted_at timestamp
        db_event.status = models.EventStatus.CANCELLED.value # marking the event as cancelled to prevent it from showing up in active listings
        db.commit()
    return db_event

def search_events(db: Session, location: str = None, is_weekend: bool = None, date: datetime = None, time_slot: str = None):
    # default active events first and sold out events later, all of these by date ascending
    query = db.query(models.Event).filter(models.Event.status == models.EventStatus.ACTIVE.value, models.Event.deleted_at == None)

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
    db_ticket = db.query(models.Ticket).filter(models.Ticket.id == booking.ticket_id).with_for_update().first() # locking the row for update to prevent race conditions
    
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
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id, models.Booking.customer_id == user_id).with_for_update().first() # locking the row for update to prevent race conditions
    
    if not booking or booking.status == models.BookingStatus.CANCELLED.value:
        return booking, []

    booking.status = models.BookingStatus.CANCELLED.value
    ticket_id = booking.ticket_id
    available_to_reassign = booking.quantity
    fulfilled_users = [] # to keep track of waitlist users who got fulfilled from this cancellation

    print(f"DEBUG: Cancelling {available_to_reassign} tickets for booking ID {ticket_id}")

    # keep fulfilling the cancelled booking quantity from the waitlist before adding back to available stock
    while available_to_reassign > 0:
        all_waiting = db.query(models.Waitlist).filter(models.Waitlist.ticket_id == ticket_id).all()
        print(f"DEBUG: Total people on waitlist for this: {len(all_waiting)}")
        
        # checking the waitlist with the first entry for same event
        waitlist_entry = db.query(models.Waitlist).filter(models.Waitlist.ticket_id == ticket_id, models.Waitlist.quantity <= available_to_reassign).order_by(models.Waitlist.created_at.asc()).with_for_update().first()

        if not waitlist_entry:
            print(f"DEBUG: No suitable waitlist entry found. Breaking loop")
            break

        print(f"DEBUG: Fulfilling waitlist for User {waitlist_entry.user_id} with {waitlist_entry.quantity} tickets")
        
        new_booking = models.Booking(customer_id=waitlist_entry.user_id, ticket_id=ticket_id, quantity=waitlist_entry.quantity, status=models.BookingStatus.CONFIRMED.value)
        db.add(new_booking)

        # track the user and their email for notification
        fulfilled_users.append({
            "email": waitlist_entry.user.email,
            "event_title": waitlist_entry.ticket.event.title,
            "quantity": waitlist_entry.quantity
        })

        available_to_reassign -= waitlist_entry.quantity
        db.delete(waitlist_entry)
        db.flush() # flushing after each assignment to update the available quantity for next waitlist entry

    if available_to_reassign > 0:
        # adding the remaining quantity back to available stock
        ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).with_for_update().first()
        if ticket:
            ticket.quantity_available += available_to_reassign
            print(f"DEBUG: Returned {available_to_reassign} tickets to genarak slot")
    
    db.commit()
    db.refresh(booking)
    return booking, fulfilled_users

def join_waitlist(db: Session, ticket_id: int, user_id: int, quantity: int):
    # not allowing to make duplicate waitlist entries for same user and ticket
    existing = db.query(models.Waitlist).filter(models.Waitlist.ticket_id == ticket_id, models.Waitlist.user_id == user_id).first()

    if existing:
        return existing
    
    # not allowing to join waitlist with quantity more than total capacity of the event
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()

    total_ever_available = ticket.quantity_available + db.query(func.sum(models.Booking.quantity)).filter(models.Booking.ticket_id == ticket_id, models.Booking.status == "confirmed").scalar() or 0

    if quantity > total_ever_available:
        return "EXCEEDS_CAPACITY"

    new_entry = models.Waitlist(ticket_id=ticket_id, user_id=user_id, quantity=quantity)
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry

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