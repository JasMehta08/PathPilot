import os
import osmnx as ox
import logging

# Define the directory where map data is stored
DATA_DIR = "data"
# Ensure the base path is relative to the project root (PathPilot)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAP_DATA_PATH = os.path.join(BASE_DIR, DATA_DIR)

logger = logging.getLogger(__name__)

# Configure OSMnx to retrieve useful tags for routing
ox.settings.useful_tags_way = list(set(ox.settings.useful_tags_way + ['surface', 'maxspeed', 'lanes', 'width']))


def get_map(place_name: str = None, network_type: str = 'drive', bbox: tuple = None, optimize: bool = True):
    """
    Downloads or loads a map from the local cache.

    Args:
        place_name (str): The name of the place to get the map for 
        network_type (str): The type of road network to download 
        bbox (tuple): Optional bounding box.
        optimize (bool): Whether to project and simplify the graph.

    Returns:
        dict: {'graph': ..., 'source': ..., 'filepath': ...}
    """
    suffix = "_optimized" if optimize else ""
    
    if bbox:
        filename = f"bbox_{bbox[0]}_{bbox[1]}_{bbox[2]}_{bbox[3]}{suffix}.graphml"
    elif place_name:
        safe_name = place_name.split(',')[0].lower().replace(' ', '_')
        filename = f"{safe_name}_{network_type}{suffix}.graphml"
    else:
        logger.error("Either place_name or bbox must be provided.")
        return {'graph': None, 'source': 'error', 'filepath': None}

    filepath = os.path.join(MAP_DATA_PATH, filename)
    
    # 1. Check cache
    if os.path.exists(filepath):
        try:
            logger.info(f"Loading map from local cache: {filepath}")
            graph = ox.load_graphml(filepath)
            return {'graph': graph, 'source': 'cache', 'filepath': filepath}
        except Exception as e:
            logger.error(f"Failed to load graphml from cache: {e}")

    # 2. Download and potentially optimize
    try:
        if bbox:
            logger.info(f"No local data found. Downloading map for bbox {bbox}...")
            G = ox.graph_from_bbox(bbox[0], bbox[1], bbox[2], bbox[3], network_type=network_type)
        else:
            logger.info(f"No local data found. Downloading map for '{place_name}'...")
            G = ox.graph_from_place(place_name, network_type=network_type)
        
        if optimize:
            logger.info("Optimizing graph...")
            # 1. Project to UTM
            G = ox.project_graph(G)
            # 2. Consolidate Intersections
            G = ox.consolidate_intersections(G, tolerance=10, rebuild_graph=True, dead_ends=True)
            # 3. Add Speeds
            G = ox.add_edge_speeds(G)
            G = ox.add_edge_travel_times(G)
        
        os.makedirs(MAP_DATA_PATH, exist_ok=True)
        ox.save_graphml(G, filepath=filepath)
        
        return {'graph': G, 'source': 'download', 'filepath': filepath}
    except Exception as e:
        logger.error(f"Failed to download or save map: {e}")
        return {'graph': None, 'source': 'error', 'filepath': None}