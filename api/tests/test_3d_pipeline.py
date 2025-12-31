import pytest
from httpx import AsyncClient, ASGITransport
from api.main import app
import os
import shutil
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_upload_video():
    """Test uploading a valid video file"""
    # Create a dummy video file
    filename = "test_video.mp4"
    content = b"fake video content"
    files = {"file": (filename, content, "video/mp4")}
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/upload", files=files)
    
    assert response.status_code == 200
    assert response.json()["filename"] == filename
    
    # Cleanup
    upload_path = f"data/uploads/{filename}"
    if os.path.exists(upload_path):
        os.remove(upload_path)

@pytest.mark.asyncio
async def test_process_non_existent_video():
    """Test processing a file that hasn't been uploaded"""
    payload = {"video_filename": "ghost_file.mp4"}
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/process", json=payload)
        
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_process_valid_video():
    """Test processing a valid video (mocking the heavy ML pipeline)"""
    filename = "valid_video.mp4"
    upload_path = f"data/uploads/{filename}"
    
    # Ensure upload dir exists
    os.makedirs("data/uploads", exist_ok=True)
    with open(upload_path, "wb") as f:
        f.write(b"fake data")
        
    # Mock the ConverterPipeline.run method to avoid actual heavy processing
    with patch("api.main.converter.run") as mock_run:
        # Mock return value to be a dummy .ply file path
        dummy_output = "temp_process/valid_video.ply"
        os.makedirs("temp_process", exist_ok=True)
        with open(dummy_output, "w") as f:
            f.write("ply header")
        
        mock_run.return_value = dummy_output
        
        payload = {"video_filename": filename}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/process", json=payload)
            
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "complete"
        assert "model_url" in data
        assert filename.replace(".mp4", ".ply") in data["model_url"]
        
        # Verify the file was copied to models dir
        expected_model_path = f"data/models/{filename.replace('.mp4', '.ply')}"
        assert os.path.exists(expected_model_path)
        
        # Cleanup
        if os.path.exists(upload_path): os.remove(upload_path)
        if os.path.exists(dummy_output): os.remove(dummy_output)
        if os.path.exists(expected_model_path): os.remove(expected_model_path)
