import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers(client):
    user_data = {"email": "urluser@example.com", "password": "password123"}
    await client.post("/auth/register", json=user_data)
    login_resp = await client.post("/auth/login", json=user_data)
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestURLs:
    async def test_create_short_url(self, client, auth_headers):
        url_data = {"original_url": "https://example.com/very/long/url"}
        response = await client.post("/urls", json=url_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert "short_url" in data
        assert "short_code" in data
        assert data["original_url"] == url_data["original_url"]
        assert data["clicks"] == 0
        assert len(data["short_code"]) == 6

    async def test_create_short_url_unauthorized(self, client):
        url_data = {"original_url": "https://example.com"}
        response = await client.post("/urls", json=url_data)
        assert response.status_code == 401

    async def test_list_urls(self, client, auth_headers):
        for i in range(3):
            await client.post("/urls", json={"original_url": f"https://example.com/{i}"}, headers=auth_headers)
        response = await client.get("/urls", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    async def test_get_url_info(self, client, auth_headers):
        create_resp = await client.post("/urls", json={"original_url": "https://example.com/info"}, headers=auth_headers)
        short_code = create_resp.json()["short_code"]
        response = await client.get(f"/urls/{short_code}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["short_code"] == short_code

    async def test_delete_url(self, client, auth_headers):
        create_resp = await client.post("/urls", json={"original_url": "https://example.com/delete"}, headers=auth_headers)
        url_id = create_resp.json()["id"]
        response = await client.delete(f"/urls/{url_id}", headers=auth_headers)
        assert response.status_code == 204

        get_resp = await client.get(f"/urls/{create_resp.json()['short_code']}", headers=auth_headers)
        assert get_resp.status_code == 404

    async def test_redirect(self, client, auth_headers):
        create_resp = await client.post("/urls", json={"original_url": "https://example.com/redirect"}, headers=auth_headers)
        short_code = create_resp.json()["short_code"]
        response = await client.get(f"/{short_code}/redirect", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "https://example.com/redirect"

    async def test_redirect_increments_clicks(self, client, auth_headers):
        create_resp = await client.post("/urls", json={"original_url": "https://example.com/clicks"}, headers=auth_headers)
        short_code = create_resp.json()["short_code"]

        await client.get(f"/{short_code}/redirect")
        await client.get(f"/{short_code}/redirect")

        info_resp = await client.get(f"/urls/{short_code}", headers=auth_headers)
        assert info_resp.json()["clicks"] == 2

    async def test_create_with_description(self, client, auth_headers):
        """Criação com descrição deve retorná-la na resposta"""
        url_data = {
            "original_url": "https://example.com/desc",
            "description": "Meu link importante"
        }
        response = await client.post("/urls", json=url_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["description"] == "Meu link importante"

    async def test_create_without_description(self, client, auth_headers):
        """Criação sem descrição deve ter description=None"""
        url_data = {"original_url": "https://example.com/nodesc"}
        response = await client.post("/urls", json=url_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["description"] is None

    async def test_description_too_long(self, client, auth_headers):
        """Descrição com mais de 500 chars deve falhar (validação Pydantic)"""
        url_data = {
            "original_url": "https://example.com/long",
            "description": "x" * 501  # 501 chars, max é 500
        }
        response = await client.post("/urls", json=url_data, headers=auth_headers)
        assert response.status_code == 422  # Unprocessable Entity (validation error)

    async def test_description_persists_in_list(self, client, auth_headers):
        """Ao listar, descrição deve estar presente"""
        await client.post("/urls", json={
            "original_url": "https://example.com/list",
            "description": "Link para listar"
        }, headers=auth_headers)
        response = await client.get("/urls", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["description"] == "Link para listar"

    async def test_description_persists_in_get(self, client, auth_headers):
        """Ao obter info, descrição deve estar presente"""
        create_resp = await client.post("/urls", json={
            "original_url": "https://example.com/get",
            "description": "Link para obter"
        }, headers=auth_headers)
        short_code = create_resp.json()["short_code"]
        response = await client.get(f"/urls/{short_code}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["description"] == "Link para obter"