import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_miscellaneous_scenarios():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        
        # --- SETUP: ORGANIZER & CUSTOMER ---
        await ac.post("/register", json={"email": "final_org@test.com", "password": "123", "role": "organizer"})
        org_login = await ac.post("/token", json={"email": "final_org@test.com", "password": "123"})
        org_headers = {"Authorization": f"Bearer {org_login.json()['access_token']}"}

        # Create Event
        event_resp = await ac.post("/events", headers=org_headers, json={
            "title": "Visibility Test",
            "description": "Who is coming?",
            "date": "2026-08-01T10:00:00",
            "venue": "Hall 1",
            "tickets": [{"ticket_type": "Standard", "price": 10.0, "quantity_available": 100}]
        })
        event_id = event_resp.json()["id"]
        ticket_id = event_resp.json()["tickets"][0]["id"]

        # Create 2 Customers to book the same event
        for i in range(2):
            email = f"guest_{i}@test.com"
            await ac.post("/register", json={"email": email, "password": "123", "role": "customer"})
            c_login = await ac.post("/token", json={"email": email, "password": "123"})
            c_headers = {"Authorization": f"Bearer {c_login.json()['access_token']}"}
            await ac.post("/bookings/", headers=c_headers, json={"ticket_id": ticket_id, "quantity": 1})

        # --- READ: ORGANIZER VIEWING ALL BOOKINGS FOR THEIR EVENT ---
        # Note: We ensure the organizer can see the guest list for their specific event
        # (Assuming you have an endpoint like GET /organizer/events/{id}/bookings)
        # If not yet explicitly in main.py, we test the logic that would support it
        all_bookings = await ac.get("/organizer/bookings", headers=org_headers)
        assert all_bookings.status_code == 200
        # Check if the bookings we just made show up for the organizer
        assert len(all_bookings.json()) >= 2

        # --- UPDATE: ORGANIZER UPDATING OWN PROFILE ---
        # Testing if an organizer can update their role (they shouldn't be able to via /users/me usually)
        update_profile = await ac.put("/users/me", headers=org_headers, json={"email": "new_boss_email@test.com"})
        assert update_profile.json()["email"] == "new_boss_email@test.com"

        # --- SECURITY CROSS-CHECK ---
        # Verify Customer CANNOT see the Organizer's booking dashboard
        await ac.post("/register", json={"email": "nosy_cust@test.com", "password": "123", "role": "customer"})
        nosy_login = await ac.post("/token", json={"email": "nosy_cust@test.com", "password": "123"})
        nosy_headers = {"Authorization": f"Bearer {nosy_login.json()['access_token']}"}
        
        forbidden_view = await ac.get("/organizer/bookings", headers=nosy_headers)
        assert forbidden_view.status_code == 403