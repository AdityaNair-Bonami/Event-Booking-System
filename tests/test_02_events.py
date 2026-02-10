import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_event_category_abundance():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        
        # --- SETUP: REGISTRATION & AUTH ---
        await ac.post("/register", json={"email": "boss@event.com", "password": "123", "role": "organizer"})
        org_login = await ac.post("/token", json={"email": "boss@event.com", "password": "123"})
        org_headers = {"Authorization": f"Bearer {org_login.json()['access_token']}"}

        # --- SUB-CATEGORY: EVENT CREATION (CREATE) ---

        # 1a. Create Event with Multiple Ticket Tiers (Abundance)
        event_data = {
            "title": "Global Tech Expo",
            "description": "The largest tech gathering of 2026",
            "date": "2026-11-15T09:00:00",
            "venue": "Convention Center",
            "tickets": [
                {"ticket_type": "Regular", "price": 50.0, "quantity_available": 500},
                {"ticket_type": "VIP", "price": 250.0, "quantity_available": 50},
                {"ticket_type": "Student", "price": 25.0, "quantity_available": 100}
            ]
        }
        create_resp = await ac.post("/events", json=event_data, headers=org_headers)
        assert create_resp.status_code == 200
        event_id = create_resp.json()["id"]
        assert len(create_resp.json()["tickets"]) == 3

        # 1b. NEGATIVE: Create Event as a Customer (Permission Check)
        await ac.post("/register", json={"email": "hacker@test.com", "password": "123", "role": "customer"})
        cust_login = await ac.post("/token", json={"email": "hacker@test.com", "password": "123"})
        cust_headers = {"Authorization": f"Bearer {cust_login.json()['access_token']}"}
        
        fail_create = await ac.post("/events", json=event_data, headers=cust_headers)
        assert fail_create.status_code == 403 # Forbidden

        # --- SUB-CATEGORY: VIEWING & DASHBOARDS (READ) ---

        # 2a. Organizer Dashboard View
        # Organizers should see their own events list
        dash_resp = await ac.get("/organizer/events", headers=org_headers)
        assert any(e["title"] == "Global Tech Expo" for e in dash_resp.json())

        # 2b. Public View (Read All)
        public_resp = await ac.get("/events/")
        assert public_resp.status_code == 200
        assert len(public_resp.json()) >= 1

        # --- SUB-CATEGORY: UPDATES & CANCELLATIONS (UPDATE) ---

        # 3a. Partial Update (Venue Change)
        update_resp = await ac.put(f"/events/{event_id}", 
            json={"venue": "New Sky Pavilion"}, 
            headers=org_headers
        )
        assert update_resp.json()["venue"] == "New Sky Pavilion"

        # 3b. SOFT DELETE: Cancel Event (Colleague's Recommendation)
        # Testing if the status flag changes to "cancelled"
        cancel_resp = await ac.put(f"/events/{event_id}", 
            json={"status": "cancelled"}, 
            headers=org_headers
        )
        assert cancel_resp.json()["status"] == "cancelled"

        # 3c. READ AFTER CANCEL: Public filtering
        # The public should NOT see cancelled events in the main list
        final_list = await ac.get("/events/")
        assert all(e["status"] != "cancelled" for e in final_list.json())

        # --- SUB-CATEGORY: HARD DELETE ---

        # 4a. Delete Event Permanently
        del_resp = await ac.delete(f"/events/{event_id}", headers=org_headers)
        assert del_resp.status_code == 200
        
        # 4b. Verify Permanent Deletion
        verify_del = await ac.get(f"/organizer/events", headers=org_headers)
        assert all(e["id"] != event_id for e in verify_del.json())