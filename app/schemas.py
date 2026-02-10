"""
Data shapes (Pydantic). This defines what the data should
look like when a user sends a request
"""

from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime


# user schemas
class UserBase(BaseModel):
    email: EmailStr
    role: str # this can be either 'organizer' or 'customer'

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class User(UserBase):
    id: int
    class Config:
        from_attributes = True


# ticket schemas
class TicketBase(BaseModel):
    ticket_type: str
    price: float
    quantity_available: int

class TicketCreate(TicketBase):
    pass

class Ticket(TicketBase):
    id: int
    event_id: int
    class Config:
        from_attributes = True


# event schemas
class EventBase(BaseModel):
    title: str
    description: str
    date: datetime
    venue: str

class EventCreate(EventBase):
    tickets: List[TicketCreate] # when creating an event, we include ticket types

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None
    venue: Optional[str] = None
    status: Optional[str] = None

class Event(EventBase):
    id: int
    organizer_id: int
    status:str
    tickets: List[Ticket] = []
    class Config:
        from_attributes = True


# booking schemas
class BookingCreate(BaseModel):
    ticket_id: int
    quantity: int

class Booking(BaseModel):
    id: int
    customer_id: int
    ticket_id: int
    quantity: int
    status: str
    class Config:
        from_attributes = True