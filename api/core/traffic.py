import random
import networkx as nx
import logging

logger = logging.getLogger(__name__)

class TrafficManager:
    """
    Simulates traffic interaction and road conditions.
    """
    
    @staticmethod
    def simulate_conditions(graph, traffic_intensity: str = "medium"):
        """
        Updates the 'travel_time' attribute of edges based on:
        1. Length / MaxSpeed (Base)
        2. Surface Factor (Unpaved is slower)
        3. Traffic Factor (Random congestion)
        """
        logger.info(f"Simulating traffic conditions (Intensity: {traffic_intensity})...")
        
        # Traffic Multipliers (1.0 = No Traffic/Free Flow)
        # Higher number = Slower (Travel time multiplier)
        if traffic_intensity == "low":
            traffic_range = (1.0, 1.2)
        elif traffic_intensity == "high":
            traffic_range = (1.5, 3.0)
        else: # medium
            traffic_range = (1.1, 1.5)
            
        # Surface Factors (Multiplier for resistance)
        # Paved = 1.0, Unpaved = 1.5
        SURFACE_PENALTY = {
            "paved": 1.0,
            "asphalt": 1.0,
            "concrete": 1.0,
            "unpaved": 1.5,
            "gravel": 1.5,
            "dirt": 2.0,
            "grass": 2.5
        }
        
        for u, v, k, data in graph.edges(keys=True, data=True):
            # 1. Base Travel Time (seconds)
            # osmnx.add_edge_travel_times calculated this from maxspeed
            base_time = data.get('travel_time', 0)
            if base_time == 0:
                 # Fallback if not calculated
                 length = data.get('length', 1)
                 speed_kph = data.get('speed_kph', 30)
                 base_time = length / (speed_kph / 3.6)
            
            # 2. Surface Factor
            surface = data.get('surface', 'paved')
            if isinstance(surface, list):
                surface = surface[0] # Handle multiple values
            
            surface_factor = SURFACE_PENALTY.get(str(surface).lower(), 1.2)
            
            # 3. Traffic Factor
            # Randomly affect main roads more?
            # For simplicity, apply random noise based on intensity
            traffic_factor = random.uniform(*traffic_range)
            
            # Store components for debug/UI (optional)
            data['traffic_factor'] = traffic_factor
            data['surface_factor'] = surface_factor
            
            # Calculate Effective Travel Time
            # time = base * surface_delay * traffic_delay
            effective_time = base_time * surface_factor * traffic_factor
            
            data['weight_time'] = effective_time
            
        logger.info("Traffic simulation complete. 'weight_time' updated on all edges.")
