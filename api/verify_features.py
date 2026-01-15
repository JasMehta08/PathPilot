import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_traffic():
    print("Testing Traffic Simulation...")
    try:
        res = requests.post(f"{BASE_URL}/traffic/simulate?intensity=high")
        res.raise_for_status()
        print("✅ Traffic Simulation Triggered:", res.json())
    except Exception as e:
        print("❌ Traffic Simulation Failed:", e)
        sys.exit(1)

def test_route_features():
    print("\nTesting Advanced Routing Features...")
    
    # Coordinates
    # Fetch from bounds to be safe
    try:
        b_res = requests.get(f"{BASE_URL}/graph/bounds")
        b_res.raise_for_status()
        bounds = b_res.json()
        print(f"   Graph Bounds: {bounds}")
        
        # Create a simple diagonal path within bounds
        # Start at 20% mark, End at 25% mark (short path to minimize risk of disconnection)
        lat_range = bounds["max_lat"] - bounds["min_lat"]
        lon_range = bounds["max_lon"] - bounds["min_lon"]
        
        start = {
            "lat": bounds["min_lat"] + lat_range * 0.45,
            "lon": bounds["min_lon"] + lon_range * 0.45
        }
        end = {
            "lat": bounds["min_lat"] + lat_range * 0.46,
            "lon": bounds["min_lon"] + lon_range * 0.46
        }
        print(f"   Testing Route: {start} -> {end}")
        
    except Exception as e:
        print("   ❌ Failed to get graph bounds:", e)
        # Fallback to hardcoded if bounds fail (unlikely if server up)
        start = {"lat": 23.2114, "lon": 72.6841} 
        end = {"lat": 23.2156, "lon": 72.6885}

    payload = {
        "start_lat": start["lat"],
        "start_lon": start["lon"],
        "end_lat": end["lat"],
        "end_lon": end["lon"],
        "weight": "weight_time"
    }
    
    try:
        res = requests.post(f"{BASE_URL}/route", json=payload)
        res.raise_for_status()
        data = res.json()
        
        # 1. Check Instructions
        if "instructions" in data and len(data["instructions"]) > 0:
            print(f"✅ Instructions Received ({len(data['instructions'])} steps)")
            print("   Sample:", data["instructions"][:3])
        else:
            print("❌ No Instructions found")
            
        # 2. Check Alternatives
        if "alternatives" in data:
            print(f"✅ Alternatives Received ({len(data['alternatives'])} routes)")
            for i, alt in enumerate(data["alternatives"]):
                print(f"   Route {i}: {alt['type']} - {alt['distance_meters']:.2f}m - {len(alt['instructions'])} steps")
        else:
            print("❌ No Alternatives found")
            
    except Exception as e:
        print("❌ Route Calculation Failed:", e)
        if 'res' in locals():
            print("   Response Body:", res.text)
        # Verify if server is even up or graph loaded
        try:
             b_res = requests.get(f"{BASE_URL}/graph/bounds")
             print("   (Graph bounds check:", b_res.status_code, ")")
        except:
             print("   (Server seems down)")
        sys.exit(1)

if __name__ == "__main__":
    test_traffic()
    test_route_features()
