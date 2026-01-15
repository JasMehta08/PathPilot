from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from api.config import settings
from api.core.map_manager import get_map
from api.routes import navigation, models

app = FastAPI(title="PathPilot API", description="Backend for 2D Maps and 3D Gaussian Splatting")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure directories exist (handled in config but good as backup or side-effect check)
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Mount static files to serve the generated 3D models
app.mount("/models", StaticFiles(directory=str(settings.MODELS_DIR)), name="models")

# Include Routers
app.include_router(navigation.router)
app.include_router(models.router)

@app.on_event("startup")
async def startup_event():
    """Pre-load the campus map on startup."""
    print(f"Loading map for {settings.CAMPUS_LOCATION}...")
    try:
        # Ensure 'temp_process' exists or create it if needed for cache?
        # Map manager handles its own caching usually.
        get_map(settings.CAMPUS_LOCATION, network_type="all")
        print("Map loaded.")
    except Exception as e:
        print(f"Warning: Could not load map: {e}")

@app.get("/")
def read_root():
    return {"status": "online", "campus": settings.CAMPUS_LOCATION}
