import time
import random
import osmnx as ox
import networkx as nx
from api.core.map_manager import get_map
from api.core.pathfinding import astar_path, euclidean_distance, haversine_distance
from pyproj import Transformer

CAMPUS_LOCATION = "Gandhinagar, India"

def run_benchmark(trials=100):
    print(f"--- Benchmarking PathPilot Optimization ({trials} trials) ---")
    print(f"Location: {CAMPUS_LOCATION}")

    # 1. Load Maps
    print("\nLoading Unoptimized Map...")
    res_old = get_map(CAMPUS_LOCATION, optimize=False)
    G_old = res_old['graph']
    
    print("Loading Optimized Map...")
    res_new = get_map(CAMPUS_LOCATION, optimize=True)
    G_new = res_new['graph']

    # Projector for Optimized Map
    projector = Transformer.from_crs("EPSG:4326", G_new.graph['crs'], always_xy=True)

    # 2. Select Random Points
    print(f"\nSelecting {trials} random start/end pairs...")
    nodes_old = list(G_old.nodes(data=True))
    test_pairs = []
    
    for _ in range(trials):
        start = random.choice(nodes_old)
        end = random.choice(nodes_old)
        # Store as Lat/Lon
        test_pairs.append(((start[1]['y'], start[1]['x']), (end[1]['y'], end[1]['x'])))

    # 3. Benchmark Old (Haversine + Unoptimized Graph)
    print("\nRunning OLD Algorithm (Haversine)...")
    start_time = time.perf_counter()
    old_success = 0
    
    for start_coords, end_coords in test_pairs:
        # Find Nearest Nodes (Lat/Lon)
        u = ox.distance.nearest_nodes(G_old, start_coords[1], start_coords[0]) 
        v = ox.distance.nearest_nodes(G_old, end_coords[1], end_coords[0])
        
        goal_coords = (G_old.nodes[v]['y'], G_old.nodes[v]['x'])
        
        def h_old(a, b):
            return haversine_distance((G_old.nodes[a]['y'], G_old.nodes[a]['x']), goal_coords)
            
        try:
            astar_path(G_old, u, v, h_old)
            old_success += 1
        except:
            pass
            
    old_duration = time.perf_counter() - start_time
    print(f"Old Time: {old_duration:.4f}s")

    # 4. Benchmark New (Euclidean + Optimized Graph)
    print("\nRunning NEW Algorithm (Euclidean + Optimization)...")
    start_time = time.perf_counter()
    new_success = 0

    for start_coords, end_coords in test_pairs:
        # Project Points
        sx, sy = projector.transform(start_coords[1], start_coords[0])
        ex, ey = projector.transform(end_coords[1], end_coords[0])
        
        # Find Nearest Nodes (Projected)
        u = ox.distance.nearest_nodes(G_new, sx, sy)
        v = ox.distance.nearest_nodes(G_new, ex, ey)
        
        goal_coords = (G_new.nodes[v]['x'], G_new.nodes[v]['y'])
        
        def h_new(a, b):
            return euclidean_distance((G_new.nodes[a]['x'], G_new.nodes[a]['y']), goal_coords)
            
        try:
            astar_path(G_new, u, v, h_new)
            new_success += 1
        except:
            pass

    new_duration = time.perf_counter() - start_time
    print(f"New Time: {new_duration:.4f}s")

    # 5. Results
    print("\n--- Results ---")
    print(f"Old System: {old_duration:.4f} seconds ({old_success}/{trials} paths found)")
    print(f"New System: {new_duration:.4f} seconds ({new_success}/{trials} paths found)")
    
    if new_duration < old_duration:
        speedup = old_duration / new_duration
        print(f"\nSpeedup: {speedup:.2f}x Faster 🚀")
    else:
        print("\nNo speedup detected.")

if __name__ == "__main__":
    run_benchmark()