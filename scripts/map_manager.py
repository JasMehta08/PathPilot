# PathPilot/scripts/map_manager.py

import os
import osmnx as ox

# Define the directory where map data is stored
DATA_DIR = "data"
# Ensure the base path is relative to the project root (PathPilot)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP_DATA_PATH = os.path.join(BASE_DIR, DATA_DIR)

def get_map(place_name: str, network_type: str = 'drive'):
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

    Returns:
        networkx.MultiDiGraph: The graph object for the specified place.
    """
    # Sanitize the place name to create a valid filename
    filename = f"{place_name.split(',')[0].lower().replace(' ', '_')}.graphml"
    filepath = os.path.join(MAP_DATA_PATH, filename)

    # 1. Check if the map data is already available
    if os.path.exists(filepath):
        print(f"Loading map for '{place_name}' from local cache: {filepath}")
        return ox.load_graphml(filepath)
    
    # 2. If not available, download and save it
    else:
        print(f"No local data found. Downloading map for '{place_name}'...")
        graph = ox.graph_from_place(place_name, network_type=network_type)
        
        # Ensure the data directory exists
        os.makedirs(MAP_DATA_PATH, exist_ok=True)
        
        print(f"💾 Saving map to {filepath}...")
        ox.save_graphml(graph, filepath=filepath)
        
        return graph