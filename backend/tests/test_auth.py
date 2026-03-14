def test_signup_login_and_me(client):
    payload = {
        "full_name": "Demo User",
        "email": "demo@test.com",
        "password": "StrongPass123!",
        "company_name": "Demo Co",
        "website": "https://demo.co",
        "industry": "Software",
    }
    signup = client.post("/auth/signup", json=payload)
    assert signup.status_code == 200
    token = signup.json()["access_token"]

    login = client.post("/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert login.status_code == 200

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == payload["email"]


def test_protected_route_requires_auth(client):
    res = client.get("/workspace")
    assert res.status_code == 401
