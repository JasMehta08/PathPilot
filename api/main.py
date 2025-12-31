from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Tuple
import networkx as nx
import osmnx as ox
import shutil
import os
from pathlib import Path
from api.core.map_manager import get_map
from api.core.pathfinding import astar_path, euclidean_distance
from api.converter.pipeline import ConverterPipeline
from pyproj import Transformer

app = FastAPI(title="PathPilot API", description="Backend for 2D Maps and 3D Gaussian Splatting")

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuration ---
CAMPUS_LOCATION = "Gandhinagar, India" 
UPLOAD_DIR = Path("data/uploads")
MODELS_DIR = Path("data/models")

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Mount static files to serve the generated 3D models
app.mount("/models", StaticFiles(directory="data/models"), name="models")

# Initialize Converter Pipeline
converter = ConverterPipeline(base_dir="temp_process")

class RouteRequest(BaseModel):
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    weight: str = "length"

class RouteResponse(BaseModel):
    path_coords: List[Tuple[float, float]]
    total_distance_meters: float
    nodes_visited: int

class ProcessRequest(BaseModel):
    video_filename: str
    use_semantics: bool = False

@app.on_event("startup")
async def startup_event():
    """Pre-load the campus map on startup."""
    print(f"Loading map for {CAMPUS_LOCATION}...")
    try:
        get_map(CAMPUS_LOCATION, network_type="all")
        print("Map loaded.")
    except Exception as e:
        print(f"Warning: Could not load map: {e}")

@app.get("/")
def read_root():
    return {"status": "online", "campus": CAMPUS_LOCATION}

@app.get("/graph/bounds")
def get_bounds():
    """Returns the lat/lon bounds of the loaded graph."""
    map_data = get_map(CAMPUS_LOCATION, network_type="all")
    G = map_data.get('graph')
    if not G:
         raise HTTPException(status_code=500, detail="Graph not loaded")
    
    nodes_data = list(G.nodes(data=True))
    
    if 'crs' in G.graph:
        # Graph is projected (meters), convert back to Lat/Lon
        inverse_projector = Transformer.from_crs(G.graph['crs'], "EPSG:4326", always_xy=True)
        xs = [data['x'] for _, data in nodes_data]
        ys = [data['y'] for _, data in nodes_data]
        lons, lats = inverse_projector.transform(xs, ys)
    else:
        # Graph is unprojected (degrees)
        lats = [data['y'] for _, data in nodes_data]
        lons = [data['x'] for _, data in nodes_data]
    
    return {
        "min_lat": min(lats),
        "max_lat": max(lats),
        "min_lon": min(lons),
        "max_lon": max(lons),
        "center": {"lat": (min(lats)+max(lats))/2, "lon": (min(lons)+max(lons))/2}
    }

from pyproj import Transformer
from api.core.pathfinding import astar_path, euclidean_distance

# ... imports ...

@app.post("/route", response_model=RouteResponse)
def compute_route(req: RouteRequest):
    map_data = get_map(CAMPUS_LOCATION, network_type="all")
    G = map_data.get('graph')
    if not G:
        raise HTTPException(status_code=500, detail="Graph not loaded")
    
    # Check if graph is projected (it should be now)
    if 'crs' not in G.graph:
         raise HTTPException(status_code=500, detail="Graph CRS not found")

    # Initialize Transformer: Lat/Lon (WGS84) -> Graph CRS
    # WGS84 is EPSG:4326. Input order for Transformer depend on initialization, usually Lat,Lon or Lon,Lat
    # pyproj < 2.0 might differ, but standard now matches strictly.
    # We'll assume standard 4326 (Lat, Lon) input if configured correctly, or Lon, Lat.
    # Note: Transformer.from_crs("EPSG:4326", G.graph['crs']) usually expects (Lat, Lon).
    
    projector = Transformer.from_crs("EPSG:4326", G.graph['crs'], always_xy=True) # inputs are (Lon, Lat) thanks to always_xy=True
    
    # Project Start/End points to Graph CRS (meters)
    start_x, start_y = projector.transform(req.start_lon, req.start_lat)
    end_x, end_y = projector.transform(req.end_lon, req.end_lat)
    
    # Find nearest nodes using projected coordinates
    origin_node = ox.distance.nearest_nodes(G, start_x, start_y)
    dest_node = ox.distance.nearest_nodes(G, end_x, end_y)
    
    goal_coords = (G.nodes[dest_node]['x'], G.nodes[dest_node]['y']) # Note: x, y for euclidean
    
    def heuristic(u, v):
        # Euclidean distance heuristic (much faster)
        return euclidean_distance((G.nodes[u]['x'], G.nodes[u]['y']), goal_coords)

    try:
        path_nodes, distance, visited = astar_path(G, origin_node, dest_node, heuristic, weight=req.weight)
    except nx.NetworkXNoPath:
        raise HTTPException(status_code=404, detail="No path found between these points")

    # Convert path nodes back to Lat/Lon for frontend
    # Inverse transformer: Graph CRS -> WGS84
    inverse_projector = Transformer.from_crs(G.graph['crs'], "EPSG:4326", always_xy=True)
    
    path_coords = []
    for node in path_nodes:
        x, y = G.nodes[node]['x'], G.nodes[node]['y']
        lon, lat = inverse_projector.transform(x, y)
        path_coords.append((lat, lon)) # Frontend expects (Lat, Lon) tuples
    
    return {
        "path_coords": path_coords,
        "total_distance_meters": distance,
        "nodes_visited": visited
    }

# --- 3D Converter Endpoints ---

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Uploads a video to the processing queue."""
    file_location = UPLOAD_DIR / file.filename
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename, "message": "Video uploaded successfully"}

@app.post("/process")
def process_video(req: ProcessRequest):
    """Triggers the 3D conversion pipeline."""
    video_path = UPLOAD_DIR / req.video_filename
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
        
    try:
        print(f"Starting pipeline for {video_path}...")
        # Note: In a real app, this should be a background task (Celery/RQ)
        output_ply = converter.run(str(video_path), use_semantics=req.use_semantics)
        
        # Copy result to models dir to be served
        final_filename = f"{req.video_filename.split('.')[0]}.ply"
        final_path = MODELS_DIR / final_filename
        shutil.copy(output_ply, final_path)
        
        return {
            "status": "complete",
            "model_url": f"http://localhost:8000/models/{final_filename}"
        }
    except Exception as e:
        print(f"Processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
