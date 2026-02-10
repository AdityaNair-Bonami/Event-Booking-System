import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_chaos_and_cleanup_abundance():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        
        # --- SETUP: ORGANIZER, EVENT, & TICKET ---
        await ac.post("/register", json={"email": "doomed_org@test.com", "password": "123", "role": "organizer"})
        org_login = await ac.post("/token", json={"email": "doomed_org@test.com", "password": "123"})
        org_headers = {"Authorization": f"Bearer {org_login.json()['access_token']}"}

        event_resp = await ac.post("/events", headers=org_headers, json={
            "title": "Fragile Event",
            "description": "Will be deleted soon",
            "date": "2026-05-01T10:00:00",
            "venue": "Test Zone",
            "tickets": [{"ticket_type": "Standard", "price": 10.0, "quantity_available": 100}]
        })
        event_id = event_resp.json()["id"]
        ticket_id = event_resp.json()["tickets"][0]["id"]

        # --- SUB-CATEGORY: THE CASCADING DELETE (DATA INTEGRITY) ---

        # 1a. Delete Organizer and verify Event disappears
        # In a real system, deleting a user should clean up their hosted events.
        await ac.delete("/users/me", headers=org_headers)
        
        # Check public events - the "Fragile Event" should be gone
        public_resp = await ac.get("/events/")
        assert all(e["id"] != event_id for e in public_resp.json())

        # --- SUB-CATEGORY: UNAUTHORIZED ROLE ACTIONS (SECURITY) ---

        # 2a. Register a fresh Customer
        await ac.post("/register", json={"email": "rebel_cust@test.com", "password": "123", "role": "customer"})
        cust_login = await ac.post("/token", json={"email": "rebel_cust@test.com", "password": "123"})
        cust_headers = {"Authorization": f"Bearer {cust_login.json()['access_token']}"}

        # 2b. NEGATIVE: Customer attempting to access Organizer Dashboard
        secret_view = await ac.get("/organizer/events", headers=cust_headers)
        assert secret_view.status_code == 403 

        # --- SUB-CATEGORY: MASS CANCELLATION FLOW ---

        # 3a. Organizer cancels event -> Notify all bookings
        # Setup: New event with a booking
        await ac.post("/register", json={"email": "active_org@test.com", "password": "123", "role": "organizer"})
        new_org_login = await ac.post("/token", json={"email": "active_org@test.com", "password": "123"})
        new_org_headers = {"Authorization": f"Bearer {new_org_login.json()['access_token']}"}

        new_event = await ac.post("/events", headers=new_org_headers, json={
            "title": "Mass Cancellation Event",
            "description": "Testing the trickle-down effect",
            "date": "2026-06-01T10:00:00",
            "venue": "Big Hall",
            "tickets": [{"ticket_type": "Entry", "price": 5.0, "quantity_available": 50}]
        })
        new_event_id = new_event.json()["id"]

        # Organizer "Soft Deletes" (Cancels) the event
        cancel_event = await ac.put(f"/events/{new_event_id}", headers=new_org_headers, json={"status": "cancelled"})
        assert cancel_event.json()["status"] == "cancelled"

        # --- SUB-CATEGORY: INPUT STRESS (VALIDATION) ---

        # 4a. NEGATIVE: Sending garbage data to /bookings/
        garbage_resp = await ac.post("/bookings/", headers=cust_headers, json={
            "ticket_id": "NOT_A_NUMBER", "quantity": "MANY"
        })
        assert garbage_resp.status_code == 422 # Pydantic validation error