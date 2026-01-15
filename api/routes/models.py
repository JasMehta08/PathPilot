from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
import shutil
from pathlib import Path
from api.config import settings
from api.converter.pipeline import ConverterPipeline

router = APIRouter()
converter = ConverterPipeline(base_dir=str(settings.TEMP_PROCESS_DIR))

class ProcessRequest(BaseModel):
    video_filename: str
    use_semantics: bool = False

@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Uploads a video to the processing queue."""
    file_location = settings.UPLOAD_DIR / file.filename
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename, "message": "Video uploaded successfully"}

@router.post("/process")
async def process_video(req: ProcessRequest):
    """Triggers the 3D conversion pipeline."""
    video_path = settings.UPLOAD_DIR / req.video_filename
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
        
    try:
        print(f"Starting pipeline for {video_path}...")
        # Run blocking processing in threadpool
        output_ply = await run_in_threadpool(converter.run, str(video_path), use_semantics=req.use_semantics)
        
        # Copy result to models dir to be served
        final_filename = f"{req.video_filename.split('.')[0]}.ply"
        final_path = settings.MODELS_DIR / final_filename
        shutil.copy(output_ply, final_path)
        
        # In a real deployed app, you'd want to return the full URL or relative path handled by frontend
        # For localhost with direct file serving:
        return {
            "status": "complete",
            "model_url": f"http://localhost:8000/models/{final_filename}"
        }
    except Exception as e:
        print(f"Processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
