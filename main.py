import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import contextily as ctx
from shapely.geometry import Point
import geopandas as gpd

# Define the area
place_name = "Lake View, Chicago, USA"
G = ox.graph_from_place(place_name, network_type='drive')

# Convert the graph to GeoDataFrames
nodes, edges = ox.graph_to_gdfs(G, nodes=True, edges=True)

# Filter out motorways
edges_filtered = edges[~edges["highway"].isin(["motorway", "motorway_link"])]

# Recreate graph from filtered edges and original nodes
G_filtered = ox.graph_from_gdfs(nodes, edges_filtered)

# Keep only the largest connected component (strongly connected for directed graph)
G_filtered = nx.subgraph(G_filtered, max(nx.strongly_connected_components(G_filtered), key=len)).copy()

# Convert to GeoDataFrames and project to Web Mercator
nodes_proj, edges_proj = ox.graph_to_gdfs(G_filtered, nodes=True, edges=True)
nodes_proj = nodes_proj.to_crs(epsg=3857)
edges_proj = edges_proj.to_crs(epsg=3857)

# Define start and end coordinates (lat, lon)
start_coord = (41.947211, -87.656506)  # Example: near Wrigley Field
end_coord = (41.935615, -87.636791)# Example: a few blocks north

# Find nearest nodes in the original unprojected graph
start_node = ox.nearest_nodes(G_filtered, X=start_coord[1], Y=start_coord[0])
end_node = ox.nearest_nodes(G_filtered, X=end_coord[1], Y=end_coord[0])

# Assign color to each node
nodes_proj["color"] = "blue"
nodes_proj.loc[start_node, "color"] = "green"
nodes_proj.loc[end_node, "color"] = "red"

# Plot
fig, ax = plt.subplots(figsize=(12, 12))

# Plot edges
edges_proj.plot(ax=ax, linewidth=1, edgecolor='black')

# Plot nodes with color
nodes_proj.plot(ax=ax, markersize=10, color=nodes_proj["color"], alpha=0.9)

# Add basemap
ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

# Clean up
ax.set_axis_off()
plt.show()