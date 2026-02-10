import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_booking_and_inventory_abundance():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        
        # --- SETUP: ORGANIZER, EVENT, & CUSTOMER ---
        # Create Organizer and an Event with limited stock
        await ac.post("/register", json={"email": "seller@test.com", "password": "123", "role": "organizer"})
        org_login = await ac.post("/token", json={"email": "seller@test.com", "password": "123"})
        org_headers = {"Authorization": f"Bearer {org_login.json()['access_token']}"}

        event_resp = await ac.post("/events", headers=org_headers, json={
            "title": "Exclusive Workshop",
            "description": "Only 10 seats available!",
            "date": "2026-12-01T10:00:00",
            "venue": "Studio 1",
            "tickets": [{"ticket_type": "Standard", "price": 100.0, "quantity_available": 10}]
        })
        event_id = event_resp.json()["id"]
        ticket_id = event_resp.json()["tickets"][0]["id"]

        # Create Customer
        await ac.post("/register", json={"email": "buyer_pro@test.com", "password": "123", "role": "customer"})
        cust_login = await ac.post("/token", json={"email": "buyer_pro@test.com", "password": "123"})
        cust_headers = {"Authorization": f"Bearer {cust_login.json()['access_token']}"}

        # --- SUB-CATEGORY: BOOKING (CREATE & MATH) ---

        # 1a. Successful Booking & Inventory Deduction
        # Buy 3 tickets. Stock should go 10 -> 7
        book_resp = await ac.post("/bookings/", headers=cust_headers, json={
            "ticket_id": ticket_id, "quantity": 3
        })
        assert book_resp.status_code == 200
        booking_id = book_resp.json()["id"]

        # Verify stock deduction
        check_event = await ac.get("/events/")
        current_stock = [t["quantity_available"] for e in check_event.json() if e["id"] == event_id for t in e["tickets"]][0]
        assert current_stock == 7

        # 1b. NEGATIVE: Over-booking (Inventory Exhaustion)
        # Try to buy 8 tickets (only 7 left). Should fail.
        fail_book = await ac.post("/bookings/", headers=cust_headers, json={
            "ticket_id": ticket_id, "quantity": 8
        })
        assert fail_book.status_code == 400
        assert "insufficient" in fail_book.json()["detail"].lower()

        # --- SUB-CATEGORY: LISTING (READ) ---

        # 2a. Customer's Personal Booking History
        history_resp = await ac.get("/bookings/my", headers=cust_headers)
        assert len(history_resp.json()) >= 1
        assert history_resp.json()[-1]["status"] == "confirmed"

        # --- SUB-CATEGORY: CANCELLATION (UPDATE/SOFT DELETE) ---

        # 3a. Cancel Booking & Inventory Return
        # Cancel the 3 tickets. Stock should go 7 -> 10
        cancel_resp = await ac.put(f"/bookings/{booking_id}/cancel", headers=cust_headers)
        assert cancel_resp.status_code == 200
        assert cancel_resp.json()["status"] == "cancelled"

        # Verify stock return
        check_event_after = await ac.get("/events/")
        returned_stock = [t["quantity_available"] for e in check_event_after.json() if e["id"] == event_id for t in e["tickets"]][0]
        assert returned_stock == 10

        # 3b. NEGATIVE: Cancel already cancelled booking
        # Should not be able to "return" tickets twice
        double_cancel = await ac.put(f"/bookings/{booking_id}/cancel", headers=cust_headers)
        assert double_cancel.status_code == 404 # Our CRUD returns None if already cancelled

        # --- SUB-CATEGORY: PERMISSION BOUNDARIES ---

        # 4a. NEGATIVE: Customer trying to cancel someone else's booking
        # Create a second customer
        await ac.post("/register", json={"email": "spy@test.com", "password": "123", "role": "customer"})
        spy_login = await ac.post("/token", json={"email": "spy@test.com", "password": "123"})
        spy_headers = {"Authorization": f"Bearer {spy_login.json()['access_token']}"}
        
        steal_cancel = await ac.put(f"/bookings/{booking_id}/cancel", headers=spy_headers)
        assert steal_cancel.status_code == 404 # Forbidden because crud.py filters by user_id