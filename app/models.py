"""
Database tables (SQLAlchemy). Handling organizers, 
customers, events, tickets, and bookings.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, Enum, select, func, case
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from .database import Base
import enum


class EventStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"

class InventoryStatus(str, enum.Enum):
    AVAILABLE = "available"
    SOLD_OUT = "sold_out"

class BookingStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

class UserRole(enum.Enum):
    ORGANIZER = "organizer"
    CUSTOMER = "customer"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)

    # relationships
    events = relationship("Event", back_populates="organizer", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="customer", cascade="all, delete-orphan")
    waitlist_entries = relationship("Waitlist", back_populates="user", cascade="all, delete-orphan")


class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    date = Column(DateTime)
    venue = Column(String)
    organizer_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default=EventStatus.ACTIVE.value)
    deleted_at = Column(DateTime, nullable=True)

    organizer = relationship("User", back_populates="events")
    tickets = relationship("Ticket", back_populates="event")

    @hybrid_property # calculates inventory status based on remaining tickets
    def inventory_status(self):
        if not self.tickets:
            return InventoryStatus.AVAILABLE.value
        total_remaining = sum(t.quantity_available for t in self.tickets)
        return InventoryStatus.AVAILABLE.value if total_remaining > 0 else InventoryStatus.SOLD_OUT.value
    
    @inventory_status.expression # allows filtering by inventory status in sorting queries
    def inventory_status(cls):
        ticket_sum_query = (
            select(func.sum(Ticket.quantity_available))
            .where(Ticket.event_id == cls.id)
            .correlate(cls)
        )
        
        ticket_sum = ticket_sum_query.scalar_subquery()

        return case(
            (func.coalesce(ticket_sum, 0) > 0, InventoryStatus.AVAILABLE.value),
            else_=InventoryStatus.SOLD_OUT.value
        )


class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    ticket_type = Column(String)  # e.g., VIP, General Admission
    price = Column(Float)
    quantity_available = Column(Integer)

    event = relationship("Event", back_populates="tickets")
    bookings = relationship("Booking", back_populates="ticket", cascade="all, delete-orphan")


class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"))
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    quantity = Column(Integer)
    status = Column(String, default=BookingStatus.CONFIRMED.value)

    customer = relationship("User", back_populates="bookings")
    ticket = relationship("Ticket", back_populates="bookings")


class Waitlist(Base):
    __tablename__ = "waitlist"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    event = relationship("Event")
    user = relationship("User", back_populates="waitlist_entries")
    ticket = relationship("Ticket")