import heapq
import math
import logging
import osmnx as ox

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def euclidean_distance(coord1, coord2):
    """
    Calculates the Euclidean distance between two (x, y) tuples.
    Assumes coordinates are projected (e.g., UTM in meters).
    """
    return math.sqrt((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2)

def haversine_distance(coord1, coord2):
    """Calculates the Haversine distance between two (lat, lon) tuples."""
    R = 6371e3  # Earth radius in meters
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

import networkx as nx
import numpy as np
try:
    import cpp_pathfinder
    CPP_AVAILABLE = True

except ImportError:
    CPP_AVAILABLE = False
    logger.warning("C++ extension not found. Falling back to NetworkX.")

# Cache for graph data to avoid re-converting on every request
_graph_cache = {}

def clear_cache():
    """Invalidates the graph cache to force re-conversion (e.g., after traffic updates)."""
    global _graph_cache
    _graph_cache = {}
    logger.info("Pathfinding Cache Cleared.")


def prepare_graph_data(graph, weight='length'):
    """
    Converts NetworkX graph to C++ compatible flat arrays (CSR-like).
    Returns: (num_nodes, row_ptr, cols, weights, x_coords, y_coords, node_to_idx, idx_to_node)
    """
    # 1. Create mapping from Node ID -> 0..N-1
    nodes = list(graph.nodes(data=True))
    node_to_idx = {node_id: i for i, (node_id, _) in enumerate(nodes)}
    idx_to_node = {i: node_id for i, (node_id, _) in enumerate(nodes)}
    num_nodes = len(nodes)
    
    # 2. Extract Coordinates
    x_coords = [data['x'] for _, data in nodes]
    y_coords = [data['y'] for _, data in nodes]
    
    # 3. Build Adjacency Arrays (CSR-like)
    # row_ptr points to the start of neighbors for each node in cols/weights
    row_ptr = [0]
    cols = []
    weights = []
    
    current_ptr = 0
    for node_id, _ in nodes:
        neighbors = graph[node_id]
        for neighbor_id, edge_data in neighbors.items():
            # Handle MultiDiGraph: edge_data is a dict of keys -> attrs
            # We take the minimum weight edge
            min_w = float('inf')
            for k, attrs in edge_data.items():
                 w = attrs.get(weight, float('inf'))
                 if w < min_w:
                     min_w = w
            
            if min_w != float('inf'):
                cols.append(node_to_idx[neighbor_id])
                weights.append(min_w)
                current_ptr += 1
        row_ptr.append(current_ptr)
        
    return (num_nodes, row_ptr, cols, weights, x_coords, y_coords, node_to_idx, idx_to_node)

def astar_path(graph, start, goal, heuristic, weight='length'):
    """
    Finds the shortest path using C++ extension if available, else NetworkX.
    Returns: A tuple of (path, total_distance, nodes_visited).
    """
    # --- C++ Optimization ---
    if CPP_AVAILABLE:
        # Check cache
        graph_id = id(graph)
        if graph_id not in _graph_cache:
            logger.info("Converting graph to C++ format...")
            _graph_cache[graph_id] = prepare_graph_data(graph, weight)
            
        num_nodes, row_ptr, cols, weights, x_coords, y_coords, node_to_idx, idx_to_node = _graph_cache[graph_id]
        
        try:
            start_idx = node_to_idx[start]
            goal_idx = node_to_idx[goal]
            
            # Call C++ Extension
            # Returns list of indices
            path_indices = cpp_pathfinder.astar(
                num_nodes, row_ptr, cols, weights, x_coords, y_coords, start_idx, goal_idx
            )
            
            if not path_indices:
                raise nx.NetworkXNoPath
                
            # Convert back to Node IDs
            path = [idx_to_node[i] for i in path_indices]
            
            # Calculate total distance (could be returned by C++ but easy to calc here or ignore)
            # For exact parity with valid return signature:
            # We can accumulate weights or just trust C++ did right. 
            # Let's quickly sum it up for the return value.
            total_distance = 0
            for i in range(len(path_indices) - 1):
                u, v = path_indices[i], path_indices[i+1]
                # We can't easily lookup edge weight in flattened arrays without searching
                # So we just query the original graph again, which is O(1) for hash map
                edge_data = min(graph.get_edge_data(path[i], path[i+1]).values(), key=lambda e: e.get(weight, float('inf')))
                total_distance += edge_data.get(weight, 0)

            logger.info(f"C++ A* found path with distance {total_distance}")
            return path, total_distance, -1 # -1 for visited count

        except (KeyError, nx.NetworkXNoPath):
             # Fallback or error if nodes not in graph
             logger.warning("C++ A* failed or no path. Falling back/Erroring.")
             pass # Fall through to Python implementation just in case? Or raise.
             # If start/end not in node_to_idx, it's a real error.
             if start not in node_to_idx or goal not in node_to_idx:
                 pass # Let NetworkX generic handler deal with it? 
             else:
                 return None, float('inf'), 0

    # --- Fallback to NetworkX ---
    try:
        # NetworkX astar_path returns just the list of nodes
        path = nx.astar_path(graph, start, goal, heuristic=heuristic, weight=weight)
        
        # Calculate distance
        total_distance = 0
        for i in range(len(path) - 1):
             u, v = path[i], path[i+1]
             edge_data = min(graph.get_edge_data(u, v).values(), key=lambda e: e.get(weight, float('inf')))
             total_distance += edge_data.get(weight, 0)
             
        return path, total_distance, -1 # -1 for visited count
    except nx.NetworkXNoPath:
        logger.info(f"NetworkX A* did not find a path.")
        return None, float('inf'), 0

def get_k_shortest_paths(graph, start, goal, heuristic, weight='length', k=3):
    """
    Finds k shortest paths using C++ A* and Penalty method.
    Returns: List of (path, distance, label) tuples.
    """
    paths = []
    
    # 1. Primary "Optimal" Path
    path_primary, dist_primary, _ = astar_path(graph, start, goal, heuristic, weight)
    if not path_primary:
        return []
    
    paths.append({"path": path_primary, "distance": dist_primary, "type": "Fastest" if weight == 'weight_time' else "Shortest"})
    
    # 2. Alternative Paths (Penalty Method)
    # Only if C++ is available (for performance), otherwise just return primary
    if not CPP_AVAILABLE:
        return paths

    # Get cached graph data
    graph_id = id(graph)
    if graph_id not in _graph_cache:
        _graph_cache[graph_id] = prepare_graph_data(graph, weight)
    
    num_nodes, row_ptr, cols, original_weights, x_coords, y_coords, node_to_idx, idx_to_node = _graph_cache[graph_id]
    
    try:
        start_idx = node_to_idx[start]
        goal_idx = node_to_idx[goal]
        
        # Working Copy of weights
        current_weights = list(original_weights)
        
        for i in range(k - 1):
            # Penalize edges in the LAST found path
            last_path = paths[-1]["path"]
            
            # Map path nodes to edges in CSR structure
            # This is tricky without an edge-lookup map from (u,v) -> index in weights
            # The CSR structure (row_ptr, cols) lets us find v in u's neighbors
            
            penalty_factor = 1.5
            
            for j in range(len(last_path) - 1):
                u_id = last_path[j]
                v_id = last_path[j+1]
                
                if u_id not in node_to_idx or v_id not in node_to_idx: continue
                u_idx = node_to_idx[u_id]
                v_idx = node_to_idx[v_id]
                
                # Find edge (u,v) in cols
                # Neighbors of u are in cols[row_ptr[u] : row_ptr[u+1]]
                start_edge_idx = row_ptr[u_idx]
                end_edge_idx = row_ptr[u_idx+1]
                
                for w_idx in range(start_edge_idx, end_edge_idx):
                    if cols[w_idx] == v_idx:
                        current_weights[w_idx] *= penalty_factor
                        break
            
            # Re-run A* with penalized weights
            path_indices = cpp_pathfinder.astar(
                num_nodes, row_ptr, cols, current_weights, x_coords, y_coords, start_idx, goal_idx
            )
            
            if not path_indices: break
            
            new_path = [idx_to_node[n] for n in path_indices]
            
            # Check duplication (simple string check)
            if str(new_path) == str(paths[-1]["path"]):
                break # Converged
                
            # Calc real distance (unpenalized)
            real_dist = 0
            for j in range(len(new_path) - 1):
                u, v = new_path[j], new_path[j+1]
                edge_data = min(graph.get_edge_data(u, v).values(), key=lambda e: e.get(weight, float('inf')))
                real_dist += edge_data.get(weight, 0)
                
            paths.append({"path": new_path, "distance": real_dist, "type": f"Alternative {i+1}"})
            
    except (KeyError, nx.NetworkXNoPath, Exception) as e:
        logger.error(f"Error finding alternatives: {e}")
        pass
        
    return paths

def dijkstra_path(graph, start, goal, weight='length'):
    """
    Finds the shortest path using Dijkstra's algorithm and counts visited nodes.
    Returns: A tuple of (path, nodes_visited).
    """
    open_set = []
    # Priority is just the distance (g_score), no heuristic
    heapq.heappush(open_set, (0, start))
    open_set_hash = {start}

    came_from = {}
    g_score = {node: float('inf') for node in graph.nodes}
    g_score[start] = 0
    
    nodes_visited = 0

    while open_set:
        current_g_score, current = heapq.heappop(open_set)
        open_set_hash.remove(current)
        nodes_visited += 1
        
        # If we've found a better path already, skip
        if current_g_score > g_score[current]:
            continue

        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            logger.info(f"Dijkstra found path with distance {g_score[goal]} after visiting {nodes_visited} nodes.")
            return path, nodes_visited

        for neighbor in graph.neighbors(current):
            edge_data = min(graph.get_edge_data(current, neighbor).values(), key=lambda e: e.get(weight, float('inf')))
            edge_weight = edge_data.get(weight, 0)
            tentative_g_score = g_score[current] + edge_weight

            if tentative_g_score < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                if neighbor not in open_set_hash:
                    heapq.heappush(open_set, (tentative_g_score, neighbor))
                    open_set_hash.add(neighbor)
    logger.info(f"Dijkstra did not find a path after visiting {nodes_visited} nodes.")
    return None, nodes_visited

def visualize_path(graph, path):
    """
    Visualizes the given path on the graph using OSMnx.
    """
    if not path:
        logger.warning("No path to visualize.")
        return
    try:
        fig, ax = ox.plot_graph_route(graph, path, route_linewidth=4, node_size=0, bgcolor='k')
        logger.info("Path visualization complete.")
    except Exception as e:
        logger.error(f"Error visualizing path: {e}")