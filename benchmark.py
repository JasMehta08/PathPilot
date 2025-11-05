# PathPilot/benchmark.py

import networkx as nx
import osmnx as ox
import random
import time
import pandas as pd
import logging

# Import our custom modules from the 'pathfinding.py' file
from scripts.map_manager import get_map
from scripts.pathfinding import astar_path as custom_astar_path
from scripts.pathfinding import dijkstra_path as custom_dijkstra_path
from scripts.pathfinding import haversine_distance

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_full_benchmark(place_name: str):
    """
    Runs a comprehensive benchmark comparing A*, Dijkstra, and their custom implementations.
    """
    logger.info("\n" + "="*60)
    logger.info(f"Starting Full Benchmark for: {place_name}")
    logger.info("="*60)

    # 1. Get map and select random nodes
    map_data = get_map(place_name)
    G = map_data.get('graph')
    if G is None:
        logger.error("Graph data not found. Exiting benchmark.")
        return

    nodes = list(G.nodes())
    origin_node, dest_node = random.sample(nodes, 2)
    logger.info(f"Finding path from node {origin_node} to {dest_node}\n")

    results = []
    weight = 'length'

    # --- Benchmark NetworkX Dijkstra ---
    start_time = time.time()
    # Get the total length of the path directly
    distance = nx.dijkstra_path_length(G, origin_node, dest_node, weight=weight)
    duration = (time.time() - start_time) * 1000
    results.append({
        'Algorithm': 'NetworkX Dijkstra',
        'Time (ms)': f"{duration:.2f}",
        'Distance (km)': f"{distance/1000:.2f}",
        'Nodes Visited': 'N/A' # Not easily available from NetworkX
    })

    # --- Benchmark Custom Dijkstra ---
    start_time = time.time()
    path_custom_dijkstra, visited_dijkstra = custom_dijkstra_path(G, origin_node, dest_node, weight=weight)
    duration = (time.time() - start_time) * 1000
    # Calculate the length of the path we found
    distance = nx.path_weight(G, path_custom_dijkstra, weight=weight)
    results.append({
        'Algorithm': 'Custom Dijkstra',
        'Time (ms)': f"{duration:.2f}",
        'Distance (km)': f"{distance/1000:.2f}",
        'Nodes Visited': visited_dijkstra
    })

    # --- Benchmark NetworkX A* ---
    start_time = time.time()
    # Get the total length of the path directly
    distance = nx.astar_path_length(G, origin_node, dest_node, weight=weight)
    duration = (time.time() - start_time) * 1000
    results.append({
        'Algorithm': 'NetworkX A*',
        'Time (ms)': f"{duration:.2f}",
        'Distance (km)': f"{distance/1000:.2f}",
        'Nodes Visited': 'N/A' # Not easily available from NetworkX
    })

    # --- Benchmark Custom A* ---
    goal_coords = (G.nodes[dest_node]['y'], G.nodes[dest_node]['x'])
    heuristic = lambda u, v: haversine_distance((G.nodes[u]['y'], G.nodes[u]['x']), goal_coords)
    start_time = time.time()
    path_custom_astar, total_distance, visited_astar = custom_astar_path(G, origin_node, dest_node, heuristic=heuristic, weight=weight)
    duration = (time.time() - start_time) * 1000
    results.append({
        'Algorithm': 'Custom A*',
        'Time (ms)': f"{duration:.2f}",
        'Distance (km)': f"{total_distance/1000:.2f}",
        'Nodes Visited': visited_astar
    })

    # --- Display Results Table ---
    df = pd.DataFrame(results)
    logger.info("--- Benchmark Results ---")
    logger.info("\n" + df.to_string(index=False))
    logger.info("-" * 60)

    # --- Visualize the shortest path (they should all be the same) ---
    logger.info("\nVisualizing the shortest path found...")
    if path_custom_astar:
        # We need the full path to plot, so we'll get it from networkx
        path_to_plot = nx.astar_path(G, origin_node, dest_node, weight=weight)
        ox.plot_graph_route(G, path_to_plot, route_color='blue', node_size=0, route_linewidth=4)
    else:
        logger.error("Could not find a path to visualize.")

if __name__ == "__main__":
    run_full_benchmark("Gandhinagar, India")