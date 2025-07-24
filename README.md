# 🛰️ PathPilot – Smart City Road Navigator

**PathPilot** is a smart, map-based routing engine tailored for cities using real-world data from **OpenStreetMap**. It enables graph-based shortest path finding (via **A\*** algorithm), and is designed to support machine learning–powered ETA prediction. Built using Python, this project emphasizes geospatial intelligence and algorithmic routing.

---

## 🌍 Project Goal

While global mapping solutions exist, many cities lack tailored routing platforms. PathPilot addresses this by:

- Extracting real urban road networks from OpenStreetMap
- Representing them as directed graphs
- Enabling shortest path computation (A*, Dijkstra, custom A*)
- Benchmarking and visualizing algorithm performance
- Structured to allow ML-based ETA prediction and congestion heatmap extensions

---

## 🛠️ Tech Stack

| Area            | Tools & Libraries                       |
|-----------------|---------------------------------------|
| Language        | Python 3.11.9                         |
| Mapping         | `OSMnx`, OpenStreetMap                |
| Graph Algorithms| `networkx`, `matplotlib`              |
| ML/Prediction   | `scikit-learn`, `pandas`, `xgboost` *(custom training pipeline being built)* |
| Optional Extras | `folium` (interactive maps), `geopandas` |

---

## 📁 Project Structure

<pre>PathPilot/
├── data/                  # Stores raw and processed map/graph data (auto-saved as .graphml)
│   └── mumbai.graphml     # (create by running the download in mumbai_map.py)
│   └── gandhinagar.graphml
│
├── scripts/               # Core scripts like A* pathfinding, data fetching
│   ├── astar.py           # Custom A* implementation
│   └── map_loader.py      # (template/empty)
│
├── different_cities/      # City-specific scripts for experiments
│   ├── mumbai_map.py      # Mumbai: load, test, and compare algorithms
│   └── gandhinagar_map.py # Gandhinagar: load, test, and compare algorithms
│
├── notebooks/             # Jupyter notebooks for exploration and ML
│   └── eta_prediction.ipynb
│
├── requirements.txt       # Python dependencies
├── README.md
└── .python-version
</pre>

---

## 🚦 Usage

### 1. **Install dependencies**
```bash
pip install -r requirements.txt
```

### 2. **Download a city map (optional, one-time per city)**
- For Mumbai: Uncomment the download lines in `different_cities/mumbai_map.py` and run the script once to save `data/mumbai.graphml`.
- For Gandhinagar: Uncomment the download lines in `different_cities/gandhinagar_map.py` and run the script once to save `data/gandhinagar.graphml`.

### 3. **Run pathfinding and benchmarking**
```bash
python different_cities/mumbai_map.py
python different_cities/gandhinagar_map.py
```
- The scripts will:
  - Load the city graph from the `data/` folder
  - Randomly select two connected nodes
  - Run and compare NetworkX Dijkstra, NetworkX A*, and custom A* algorithms
  - Print path length, time, nodes visited, and total path cost for each
  - Plot the computed paths for visual comparison

### 4. **Custom Experiments**
- Modify the scripts in `different_cities/` to select specific nodes, cities, or to add new algorithms.
- Use `scripts/astar.py` as a template for your own pathfinding logic.

---

## 🧠 Extending for Machine Learning
- The project is structured to allow integration of ML models for ETA prediction and dynamic edge weighting.
- See `notebooks/eta_prediction.ipynb` (template) for starting ML experiments.
- ML model input: simulated route features such as distance, node count, and edge metadata.
- Planned output: ETA prediction using regression models (e.g., RandomForest, XGBoost).
- Custom dataset generator in progress using randomized node pairs with route statistics.

---

## 📝 Notes
- **Do not re-download city maps every run.** Download once, then comment out the download lines to avoid API rate limits and speed up experiments.
- All scripts are modular and can be extended for new cities or algorithms.

---

## 📢 Contributing
Pull requests and issues are welcome! Please document new scripts and update the README as needed.
