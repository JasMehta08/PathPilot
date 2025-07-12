import osmnx as ox

city = "Gandhinagar, India"
G = ox.graph_from_place(city, network_type='drive')
ox.plot_graph(G)