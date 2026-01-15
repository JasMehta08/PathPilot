from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Tuple, Optional
import networkx as nx
import osmnx as ox
from pyproj import Transformer
from api.core.map_manager import get_map
from api.core.pathfinding import astar_path, euclidean_distance, clear_cache, get_k_shortest_paths
from api.core.traffic import TrafficManager
from api.config import settings
import math
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class RouteRequest(BaseModel):
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    weight: str = 'length'

class RoutePath(BaseModel):
    path_coords: list[tuple[float, float]]
    distance_meters: float
    type: str # 'Fastest', 'Shortest', 'Alternative'
    instructions: list[str]

class RouteResponse(BaseModel):
    path_coords: list[tuple[float, float]]
    total_distance_meters: float
    nodes_visited: int
    instructions: list[str]
    alternatives: list[RoutePath] = []

# Cache the transformer at module level
_projector_cache = {}

def get_projector(crs_from, crs_to):
    key = (crs_from, crs_to)
    if key not in _projector_cache:
        _projector_cache[key] = Transformer.from_crs(crs_from, crs_to, always_xy=True)
    return _projector_cache[key]

def get_bearing(lat1, lon1, lat2, lon2):
    """Calculates bearing between two points."""
    dLon = math.radians(lon2 - lon1)
    y = math.sin(dLon) * math.cos(math.radians(lat2))
    x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - \
        math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(dLon)
    brng = math.atan2(y, x)
    brng = math.degrees(brng)
    return (brng + 360) % 360

def get_turn_instruction(bearing1, bearing2):
    """Determines turn direction based on bearing change."""
    diff = (bearing2 - bearing1 + 360) % 360
    if 45 <= diff < 135:
        return "Turn Right"
    elif 225 <= diff < 315:
        return "Turn Left"
    elif 315 <= diff or diff < 45:
        return "Continue"
    elif 135 <= diff < 225:
        return "Make a U-Turn"
    return "Continue"

def generate_instructions(G, path_nodes, inverse_projector, weight_key):
    """Refactored instruction generator"""
    instructions = []
    if len(path_nodes) > 1:
        instructions.append("Start your journey")
        
    last_bearing = None
    accumulated_dist = 0
    current_street = None
    
    path_coords = []
    
    for i in range(len(path_nodes)):
        node = path_nodes[i]
        x, y = G.nodes[node]['x'], G.nodes[node]['y']
        lon, lat = inverse_projector.transform(x, y)
        path_coords.append((lat, lon))
        
        if i < len(path_nodes) - 1:
            next_node = path_nodes[i+1]
            # Use safe retrieval for edge data, as multiple edges might exist
            edges = G.get_edge_data(node, next_node)
            if edges:
                edge_data = min(edges.values(), key=lambda e: e.get(weight_key, float('inf')))
                street_name = edge_data.get('name', 'unnamed road')
                if isinstance(street_name, list): street_name = street_name[0]
                dist = edge_data.get('length', 0)
                accumulated_dist += dist

                nx_next = G.nodes[next_node]
                n_lon, n_lat = inverse_projector.transform(nx_next['x'], nx_next['y'])
                current_bearing = get_bearing(lat, lon, n_lat, n_lon)
                
                if last_bearing is not None:
                    turn = get_turn_instruction(last_bearing, current_bearing)
                    if turn != "Continue":
                        instructions.append(f"{turn} onto {street_name}")
                        accumulated_dist = 0
                
                if current_street is not None and street_name != current_street:
                     if accumulated_dist > 5:
                        instructions.append(f"Continue on {street_name}")
                
                current_street = street_name
                last_bearing = current_bearing
            
    instructions.append("Arrive at destination")
    return path_coords, instructions

@router.post("/route", response_model=RouteResponse)
def compute_route(req: RouteRequest):
    map_data = get_map(settings.CAMPUS_LOCATION, network_type="all")
    G = map_data.get('graph')
    if not G: raise HTTPException(status_code=500, detail="Graph not loaded")
    if 'crs' not in G.graph: raise HTTPException(status_code=500, detail="Graph CRS not found")
    
    # Use cached projector
    projector = get_projector("EPSG:4326", G.graph['crs'])
    start_x, start_y = projector.transform(req.start_lon, req.start_lat)
    end_x, end_y = projector.transform(req.end_lon, req.end_lat)
    
    origin_node = ox.distance.nearest_nodes(G, start_x, start_y)
    dest_node = ox.distance.nearest_nodes(G, end_x, end_y)
    goal_coords = (G.nodes[dest_node]['x'], G.nodes[dest_node]['y'])
    
    def heuristic(u, v): return euclidean_distance((G.nodes[u]['x'], G.nodes[u]['y']), goal_coords)

    # Use k-shortest paths
    paths_data = get_k_shortest_paths(G, origin_node, dest_node, heuristic, weight=req.weight, k=3)
    
    if not paths_data:
        raise HTTPException(status_code=404, detail="No path found")

    inverse_projector = get_projector(G.graph['crs'], "EPSG:4326")
    
    # Output structure
    alternatives_resp = []
    
    for p_data in paths_data:
        p_nodes = p_data["path"]
        p_coords, p_instr = generate_instructions(G, p_nodes, inverse_projector, req.weight)
        
        alternatives_resp.append(RoutePath(
            path_coords=p_coords,
            distance_meters=p_data["distance"],
            type=p_data["type"],
            instructions=p_instr
        ))
    
    # Primary (First) Path
    primary = alternatives_resp[0]
    
    return {
        "path_coords": primary.path_coords,
        "total_distance_meters": primary.distance_meters,
        "nodes_visited": -1,
        "instructions": primary.instructions,
        "alternatives": alternatives_resp # Includes primary
    }

@router.post("/traffic/simulate")
def simulate_traffic(intensity: str = "medium"):
    map_data = get_map(settings.CAMPUS_LOCATION, network_type="all")
    G = map_data.get('graph')
    if not G:
        raise HTTPException(status_code=500, detail="Graph not loaded")
    
    TrafficManager.simulate_conditions(G, intensity)
    
    # Invalidate cache for C++ pathfinder
    clear_cache()
    
    return {"message": f"Traffic simulation applied with intensity: {intensity}"}

@router.get("/graph/bounds")
def get_bounds():
    """Returns the lat/lon bounds of the loaded graph."""
    map_data = get_map(settings.CAMPUS_LOCATION, network_type="all")
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
