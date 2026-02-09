"""
Database tables (SQLAlchemy). Handling organizers, 
customers, events, tickets, and bookings.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, Enum
from sqlalchemy.orm import relationship
from .database import Base
import enum


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
    events = relationship("Event", back_populates="organizer")
    bookings = relationship("Bookings", back_populates="customer")


class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    date = Column(DateTime)
    venue = Column(String)
    organizer_id = Column(Integer, ForeignKey("users.id"))

    organizer = relationship("User", back_populates="events")
    tickets = relationship("Ticket", back_populates="event")


class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    ticket_type = Column(String)  # e.g., VIP, General Admission
    price = Column(Float)
    quantity_available = Column(Integer)

    event = relationship("Event", back_populates="tickets")
    bookings = relationship("Booking", back_populates="ticket")


class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"))
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    quantity = Column(Integer)

    customer = relationship("User", back_populates="bookings")
    ticket = relationship("Ticket", back_populates="bookings")


