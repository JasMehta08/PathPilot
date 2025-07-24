import heapq
import math

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

def astar_path(graph, start, goal, heuristic, weight='length'):
    """
    Finds the shortest path using the A* algorithm and counts visited nodes.
    Returns: A tuple of (path, nodes_visited).
    """
    open_set = []
    heapq.heappush(open_set, (heuristic(start), start))
    open_set_hash = {start}

    came_from = {}
    g_score = {node: float('inf') for node in graph.nodes}
    g_score[start] = 0
    
    nodes_visited = 0

    while open_set:
        current = heapq.heappop(open_set)[1]
        open_set_hash.remove(current)
        nodes_visited += 1

        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return path, nodes_visited

        for neighbor in graph.neighbors(current):
            edge_data = min(graph.get_edge_data(current, neighbor).values(), key=lambda e: e.get(weight, float('inf')))
            edge_weight = edge_data.get(weight, 0)
            tentative_g_score = g_score[current] + edge_weight

            if tentative_g_score < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score = tentative_g_score + heuristic(neighbor)
                if neighbor not in open_set_hash:
                    heapq.heappush(open_set, (f_score, neighbor))
                    open_set_hash.add(neighbor)
    return None, nodes_visited

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
    return None, nodes_visited