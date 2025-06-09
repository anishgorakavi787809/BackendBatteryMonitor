import pytest
from httpx import AsyncClient
from httpx import ASGITransport
from app import app  # adjust the import to your actual file structure

@pytest.mark.asyncio
async def test_update_battery():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/update_battery", json={"id": "test-device", "battery": 25})
        assert response.status_code == 200
        assert response.json()["status"] == "warning"

@pytest.mark.asyncio
async def test_view_device():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/status/test-device")
        assert response.status_code == 200
        assert response.json()["battery"] == 25

@pytest.mark.asyncio
async def test_view_all():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/status")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_delete_device():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.delete("/remove/test-device")
        assert response.status_code == 200
        assert response.json()["message"] == "Device removed"
