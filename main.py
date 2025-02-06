import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt

# Define the area
place_name = "Lake View, Chicago, USA"
G = ox.graph_from_place(place_name, network_type='drive')

# Convert the graph to GeoDataFrames
nodes, edges = ox.graph_to_gdfs(G, nodes=True, edges=True)

# Filter out motorway roads
edges_filtered = edges[~edges["highway"].isin(["motorway", "motorway_link"])]

# Convert back to a graph
G_filtered = ox.graph_from_gdfs(nodes, edges_filtered)

# Create the plot
fig, ax = ox.plot_graph(G_filtered, node_size=20, node_color='red', edge_linewidth=1, bgcolor="white", show=False, close=False)

# Show the figure
plt.show()
