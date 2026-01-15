#include <vector>
#include <queue>
#include <cmath>
#include <limits>
#include <algorithm>
#include <iostream>

// Simple Node structure for priority queue
struct Node {
    int id;
    float f_score;

    bool operator>(const Node& other) const {
        return f_score > other.f_score;
    }
};

// Heuristic function (Euclidean distance)
float heuristic(int u, int goal, const std::vector<float>& x, const std::vector<float>& y) {
    float dx = x[u] - x[goal];
    float dy = y[u] - y[goal];
    return std::sqrt(dx*dx + dy*dy);
}

// A* Algorithm
// graph indices: 0 to num_nodes-1
// row_ptr, cols, weights: CSR-like format or simple Adjacency List flattened
// We will use a simplified format:
// For now, let's accept a full Adjacency List passed as flat arrays for simplicity in integration
// But constructing that in Python might be slow.
// Better: Python passes "indices" and "indptr" from a scipy sparse matrix?
// Or just plain old list of lists converted to flattened arrays?
// Let's assume simpler input from Python: 
// row_ptr[i] is start index in cols/weights for node i
// row_ptr[i+1] is end index
std::vector<int> astar_cpp(
    int num_nodes,
    const std::vector<int>& row_ptr,
    const std::vector<int>& cols,
    const std::vector<float>& weights,
    const std::vector<float>& x_coords,
    const std::vector<float>& y_coords,
    int start_node,
    int goal_node
) {
    std::vector<float> g_score(num_nodes, std::numeric_limits<float>::infinity());
    std::vector<int> came_from(num_nodes, -1);
    std::vector<bool> visited(num_nodes, false);

    std::priority_queue<Node, std::vector<Node>, std::greater<Node>> open_set;

    g_score[start_node] = 0.0f;
    open_set.push({start_node, heuristic(start_node, goal_node, x_coords, y_coords)});

    while (!open_set.empty()) {
        Node current = open_set.top();
        open_set.pop();

        int u = current.id;

        if (u == goal_node) {
            // Reconstruct path
            std::vector<int> path;
            int curr = goal_node;
            while (curr != -1) {
                path.push_back(curr);
                curr = came_from[curr];
            }
            std::reverse(path.begin(), path.end());
            return path;
        }

        // Lazy deletion logic: if we found a better path to u already, skip
        // But since we don't have a modify-key PQ, we just push duplicates.
        // We can check if g_score is worse than stored.
        // But f_score check from PQ pop is tricky without exact g_score matching.
        // Standard lazy: check if we closed it already?
        // Note: A* with consistent heuristic doesn't need re-expansion.
        // But simpler: just check if g_score matches.
        
        // Actually simpler logic for standard Dijkstra/A*:
        // if (current.f_score > g_score[u] + h(u)) -> effectively checking if stale
        // But f_score includes h. 
        // Let's just do:
        // if (current_g > g_score[u]) continue; 
        // We'd need to store g in Node to do that efficiently.
        // Let's rely on standard relaxation.

        int start_edge = row_ptr[u];
        int end_edge = row_ptr[u+1];

        for (int i = start_edge; i < end_edge; ++i) {
            int v = cols[i];
            float w = weights[i];

            float tentative_g = g_score[u] + w;
            if (tentative_g < g_score[v]) {
                came_from[v] = u;
                g_score[v] = tentative_g;
                float f = tentative_g + heuristic(v, goal_node, x_coords, y_coords);
                open_set.push({v, f});
            }
        }
    }

    return {}; // No path found
}
