# 🛰️ PathPilot – Smart City Road Navigator

**PathPilot** is a smart, map-based routing engine tailored for small cities using real-world data from **OpenStreetMap**. It enables graph-based shortest path finding (via **A\*** algorithm), with plans for machine learning–powered ETA prediction. Built using Python, this project emphasizes geospatial intelligence and algorithmic routing.

---

## 🌍 Project Goal

While global mapping solutions exist, many small cities lack tailored routing platforms. PathPilot addresses this by:

- Extracting real urban road networks from OpenStreetMap
- Representing them as directed graphs
- Enabling shortest path computation (e.g., A\* algorithm)
- Planning for future extensions like ML-based ETA and congestion heatmaps

---

## 🛠️ Tech Stack

| Area            | Tools & Libraries                      |
|------------------|----------------------------------------|
| Language         | Python 3.11.9                          |
| Mapping          | `OSMnx`, OpenStreetMap                 |
| Graph Algorithms | `networkx`, `matplotlib`               |
| ML/Prediction    | `scikit-learn`, `pandas` *(planned)*   |
| Optional Extras  | `folium` (interactive maps), `geopandas` |

---

## 📁 Project Structure

<pre>

PathPilot/
├── data/                  # Stores raw and processed map/graph data
│   └── gandhinagar.graphml
│
├── scripts/               # Core scripts like A* pathfinding, data fetching
│   ├── astar.py
│   └── map_loader.py
│
├── notebooks/             # Jupyter notebooks for exploration and ML
│   └── eta_prediction.ipynb
│
├── gandhinagar_map.py     # Minimal script to load and plot the city map
├── requirements.txt
├── README.md
└── .python-version

</pre>
