import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_auth_and_profile_abundance():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        
        # --- SUB-CATEGORY: REGISTRATION (CREATE) ---
        
        # 1a. Successful Registration (Customer)
        reg_cust = await ac.post("/register", json={
            "email": "abundant_cust@test.com", "password": "secure_pass_123", "role": "customer"
        })
        assert reg_cust.status_code == 200
        assert reg_cust.json()["role"] == "customer"

        # 1b. Successful Registration (Organizer)
        reg_org = await ac.post("/register", json={
            "email": "abundant_org@test.com", "password": "secure_pass_456", "role": "organizer"
        })
        assert reg_org.status_code == 200

        # 1c. NEGATIVE: Duplicate Email (Uniqueness Constraint)
        dup_resp = await ac.post("/register", json={
            "email": "abundant_cust@test.com", "password": "different_pass", "role": "customer"
        })
        assert dup_resp.status_code == 400
        assert "already registered" in dup_resp.json()["detail"].lower()

        # 1d. NEGATIVE: Invalid Email Format (Pydantic Validation)
        invalid_email = await ac.post("/register", json={
            "email": "not-an-email", "password": "123", "role": "customer"
        })
        assert invalid_email.status_code == 422 # Unprocessable Entity

        # --- SUB-CATEGORY: LOGIN & TOKENS (READ) ---

        # 2a. Successful Login
        login_resp = await ac.post("/token", json={
            "email": "abundant_cust@test.com", "password": "secure_pass_123"
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2b. NEGATIVE: Wrong Password
        wrong_pass = await ac.post("/token", json={
            "email": "abundant_cust@test.com", "password": "wrong_password"
        })
        assert wrong_pass.status_code == 401

        # 2c. NEGATIVE: Access Protected Route without Token
        no_auth = await ac.get("/bookings/my")
        assert no_auth.status_code == 401

        # --- SUB-CATEGORY: PROFILE UPDATES (UPDATE) ---

        # 3a. Update Email Successfully
        update_resp = await ac.put("/users/me", 
            json={"email": "new_email@test.com"}, 
            headers=headers
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["email"] == "new_email@test.com"

        # 3b. Verify Login with New Email
        new_login = await ac.post("/token", json={
            "email": "new_email@test.com", "password": "secure_pass_123"
        })
        assert new_login.status_code == 200

        # --- SUB-CATEGORY: DELETION (HARD DELETE) ---

        # 4a. Delete Self (Customer)
        # Using the new_login token headers
        new_headers = {"Authorization": f"Bearer {new_login.json()['access_token']}"}
        del_resp = await ac.delete("/users/me", headers=new_headers)
        assert del_resp.status_code == 200
        assert "deleted" in del_resp.json()["message"].lower()

        # 4b. Verify User is Gone (Try to login again)
        gone_login = await ac.post("/token", json={
            "email": "new_email@test.com", "password": "secure_pass_123"
        })
        assert gone_login.status_code == 401