import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


class TestAuth:
    async def test_register(self, client):
        user_data = {"email": "test@example.com", "password": "password123"}
        response = await client.post("/auth/register", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert "id" in data
        assert data["is_active"] is True

    async def test_register_duplicate_email(self, client):
        user_data = {"email": "dup@example.com", "password": "password123"}
        await client.post("/auth/register", json=user_data)
        response = await client.post("/auth/register", json=user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    async def test_login(self, client):
        user_data = {"email": "login@example.com", "password": "password123"}
        await client.post("/auth/register", json=user_data)
        response = await client.post("/auth/login", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_credentials(self, client):
        user_data = {"email": "login2@example.com", "password": "password123"}
        await client.post("/auth/register", json=user_data)
        response = await client.post("/auth/login", json={"email": "login2@example.com", "password": "wrong"})
        assert response.status_code == 401

    async def test_get_me(self, client):
        user_data = {"email": "me@example.com", "password": "password123"}
        await client.post("/auth/register", json=user_data)
        login_resp = await client.post("/auth/login", json=user_data)
        token = login_resp.json()["access_token"]
        response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["email"] == user_data["email"]