import os
import osmnx as ox
import logging

# Define the directory where map data is stored
DATA_DIR = "data"
# Ensure the base path is relative to the project root (PathPilot)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP_DATA_PATH = os.path.join(BASE_DIR, DATA_DIR)

logger = logging.getLogger(__name__)

def get_map(place_name: str = None, network_type: str = 'drive', bbox: tuple = None):
    """
    Downloads or loads a map from the local cache.

    Checks if a GraphML file for the given place exists in the data directory.
    If it exists, it loads the map from the file.
    If not, it downloads the map using OSMnx, saves it to the directory,
    and then returns the graph.

    Args:
        place_name (str): The name of the place to get the map for 
                          (e.g., "Gandhinagar, India").
        network_type (str): The type of road network to download 
                            (e.g., 'drive', 'walk', 'bike').
        bbox (tuple): Optional bounding box to fetch map as (north, south, east, west).

    Returns:
        dict: {
            'graph': networkx.MultiDiGraph or None,
            'source': 'cache' or 'download' or 'error',
            'filepath': str or None
        }
    """
    if bbox:
        filename = f"bbox_{bbox[0]}_{bbox[1]}_{bbox[2]}_{bbox[3]}.graphml"
    elif place_name:
        filename = f"{place_name.split(',')[0].lower().replace(' ', '_')}.graphml"
    else:
        logger.error("Either place_name or bbox must be provided.")
        return {'graph': None, 'source': 'error', 'filepath': None}

    filepath = os.path.join(MAP_DATA_PATH, filename)

    # 1. Check if the map data is already available
    if os.path.exists(filepath):
        try:
            logger.info(f"Loading map from local cache: {filepath}")
            graph = ox.load_graphml(filepath)
            return {'graph': graph, 'source': 'cache', 'filepath': filepath}
        except Exception as e:
            logger.error(f"Failed to load graphml from cache: {e}")

    # 2. If not available or loading failed, download and save it
    try:
        if bbox:
            logger.info(f"No local data found. Downloading map for bbox {bbox}...")
            graph = ox.graph_from_bbox(bbox[0], bbox[1], bbox[2], bbox[3], network_type=network_type)
        else:
            logger.info(f"No local data found. Downloading map for '{place_name}'...")
            graph = ox.graph_from_place(place_name, network_type=network_type)
        
        # Ensure the data directory exists
        os.makedirs(MAP_DATA_PATH, exist_ok=True)
        
        logger.info(f"Saving map to {filepath}...")
        ox.save_graphml(graph, filepath=filepath)
        
        return {'graph': graph, 'source': 'download', 'filepath': filepath}
    except Exception as e:
        logger.error(f"Failed to download or save map: {e}")
        return {'graph': None, 'source': 'error', 'filepath': None}