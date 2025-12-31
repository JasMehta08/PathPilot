import pytest
from httpx import AsyncClient, ASGITransport
from api.main import app
import math

# Use the same default location as the app for consistent testing
CAMPUS_LOCATION = "Gandhinagar, India"

@pytest.mark.asyncio
async def test_read_root():
    """Test the root endpoint status"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

@pytest.mark.asyncio
async def test_get_bounds():
    """Test getting map bounds"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/graph/bounds")
    assert response.status_code == 200
    data = response.json()
    assert "min_lat" in data
    assert "max_lat" in data
    assert "center" in data

@pytest.mark.asyncio
async def test_valid_route():
    """Test finding a route between two valid points"""
    # Use bounds to find some valid points within the map area
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        bounds_res = await ac.get("/graph/bounds")
        bounds = bounds_res.json()
        
        # Pick two points slightly offset from center
        center = bounds["center"]
        start_lat = center["lat"] - 0.001
        start_lon = center["lon"] - 0.001
        end_lat = center["lat"] + 0.001
        end_lon = center["lon"] + 0.001
        
        payload = {
            "start_lat": start_lat,
            "start_lon": start_lon,
            "end_lat": end_lat,
            "end_lon": end_lon,
            "weight": "length"
        }
        
        response = await ac.post("/route", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["path_coords"]) > 0
    assert data["total_distance_meters"] > 0
    assert data["nodes_visited"] > 0

@pytest.mark.asyncio
async def test_start_equals_end():
    """Test route with identical start and end points"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        bounds_res = await ac.get("/graph/bounds")
        center = bounds_res.json()["center"]
        
        payload = {
            "start_lat": center["lat"],
            "start_lon": center["lon"],
            "end_lat": center["lat"],
            "end_lon": center["lon"]
        }
        
        response = await ac.post("/route", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    # Distance should be effectively 0 (or extremely small due to nearest node snapping)
    # If it matched the exact node, distance is 0. If it snapped to same node, 0.
    assert data["total_distance_meters"] < 1.0 

@pytest.mark.asyncio
async def test_invalid_coordinates():
    """Test validation error for missing fields"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "start_lat": "invalid", # String instead of float
            "start_lon": 0.0,
            # Missing end points
        }
        response = await ac.post("/route", json=payload)
    
    # Validation error
    assert response.status_code == 422
