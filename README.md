# 🎟️ Event Management & Booking System

An asynchronous Event Booking API designed for high performance and scalability. 
This system utilizes **FastAPI** for its core logic, **SQLAlchemy** for robust data persistence, 
and **Celery** with **Redis** to handle intensive background tasks like email notifications without 
interrupting the user experience.

---

## 🚀 System Architecture & Features

This project is built to demonstrate modern backend practices, including:
* **Asynchronous Task Processing:** Offloads heavy operations (notifications/logging) to Celery workers via Redis.
* **Role-Based Access Control (RBAC):** Secure permission layers for 'Organizers' (creation/management) and 'Customers' (discovery/booking).
* **Automated Inventory Logic:** Real-time ticket tracking with atomic updates to prevent overselling.
* **Interactive OpenAPI Documentation:** Fully integrated Swagger UI for seamless testing and discovery.

---

## 🛠️ Tech Stack
* **Framework:** FastAPI (Python 3.12+)
* **Database:** SQLite (SQLAlchemy ORM)
* **Task Queue:** Celery + Redis
* **Security:** JWT Authentication (OAuth2 Password Bearer)
* **Environment:** Linux (Ubuntu/Debian)

---

## 📦 Installation & Quick Start

Follow these steps to set up the environment and launch the system on your local machine:

### 1. Environment Setup
```bash
# Clone the repository
git clone https://github.com/AdityaNair-Bonami/Event-Booking-System
cd "Event Management"

# Clean up old environments and initialize a fresh Linux venv
rm -rf venv .venv
sudo apt update && sudo apt install python3.12-venv
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```
### 2. Launching Services (Run in separate terminal tabs)
Ensure you have activated your virtual environment (source .venv/bin/activate) in each new tab.
* ### Tab 1 (The API)
```bash
uvicorn app.main:app --reload
```
* ### Tab 2 (Redis Service)
```bash
sudo service redis-server start
```
* ### Tab 3 (Celery)
```bash
PYTHONPATH=. celery -A app.tasks.celery_app worker --loglevel=info
```
### 3. Manual Testing & Demonstration Flow
To verify the system end-to-end, open your browser to `http://127.0.0.1:8000/docs` and perform the following sequence:

* **Identity Setup**: Use `POST /register` to create an Organizer and a Customer.
* **Authentication**: Click the green **Authorize** button. Enter the Organizer's email in the `username` field and their `password`. This "locks" the session for all subsequent requests.
* **Organizer Workflow**: Navigate to `POST /events` to create a new event. Ensure you include a `tickets` object with a set `quantity_available`.
* **Customer Workflow**: Switch users by Authorizing as the **Customer**. Use `POST /bookings/` to reserve a ticket.
* **Asynchronous Verification**: Watch your **Celery terminal tab**. You will see the `send_booking_confirmation` task fire immediately upon a successful booking, simulating a real-world email dispatch.
* **Integrity Check**: Call `GET /events/` to observe the `quantity_available` automatically decrease.

### 4. Maintenance
To reset the system to a clean state for a new demonstration:
```bash
python3 reset_db.py
```
