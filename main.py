import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import contextily as ctx
import itertools

# --- 1. Get and filter graph ---

place_name = "Lake View, Chicago, USA"
G = ox.graph_from_place(place_name, network_type='drive')

# Convert to GeoDataFrames
nodes, edges = ox.graph_to_gdfs(G, nodes=True, edges=True)

# Filter out motorways
edges_filtered = edges[~edges["highway"].isin(["motorway", "motorway_link"])]

# Recreate graph from filtered edges and original nodes
G_filtered = ox.graph_from_gdfs(nodes, edges_filtered)

# Keep largest strongly connected component (for directed graph)
G_filtered = nx.subgraph(G_filtered, max(nx.strongly_connected_components(G_filtered), key=len)).copy()

# --- 2. Define start and end coordinates ---

start_coord = (41.947211, -87.656506)  # near Wrigley Field
end_coord = (41.935615, -87.636791)    # a few blocks north

# Find nearest nodes
start_node = ox.nearest_nodes(G_filtered, X=start_coord[1], Y=start_coord[0])
end_node = ox.nearest_nodes(G_filtered, X=end_coord[1], Y=end_coord[0])

# --- 3. Prepare graph for Chinese Postman Problem (CPP) ---

# Convert to undirected graph (CPP usually on undirected graphs)
Gu = G_filtered.to_undirected()

# --- 4. Find odd degree nodes ---
odd_nodes = [n for n, d in Gu.degree() if d % 2 == 1]

# --- 5. Compute pairwise shortest path distances between odd nodes ---
odd_pairs = list(itertools.combinations(odd_nodes, 2))
distances = {}
for u, v in odd_pairs:
    distances[(u, v)] = nx.shortest_path_length(Gu, u, v, weight='length')

# --- 6. Build graph for matching with negative weights (to minimize total length) ---
odd_graph = nx.Graph()
for (u, v), dist in distances.items():
    odd_graph.add_edge(u, v, weight=-dist)

# --- 7. Find minimum weight perfect matching ---
matches = nx.algorithms.matching.max_weight_matching(odd_graph, maxcardinality=True)

# --- 8. Add duplicated edges from matched pairs ---
for u, v in matches:
    path = nx.shortest_path(Gu, u, v, weight='length')
    # Add edges along the path to Gu
    for i in range(len(path) - 1):
        edge_data = Gu.get_edge_data(path[i], path[i + 1])
        # Sometimes there are multiple edges (multigraph), take the first one:
        if isinstance(edge_data, dict) and 0 in edge_data:
            edge_data = edge_data[0]
        Gu.add_edge(path[i], path[i + 1], **edge_data)

# --- 9. Find Eulerian circuit covering all edges ---
circuit = list(nx.eulerian_circuit(Gu))

# --- 10. Calculate total length in miles ---
total_length_meters = 0
for u, v in circuit:
    # Gu[u][v] is a dict keyed by edge keys, get length of the first edge found
    edge_data = next(iter(Gu[u][v].values()))
    total_length_meters += edge_data['length']

total_length_miles = total_length_meters / 1609.344
print(f"Length of route: {total_length_miles:.2f} miles")

# --- 11. Prepare to plot ---

# Get nodes and edges GeoDataFrames of Eulerian graph, project to Web Mercator for basemap
nodes_proj, edges_proj = ox.graph_to_gdfs(Gu, nodes=True, edges=True)
nodes_proj = nodes_proj.to_crs(epsg=3857)
edges_proj = edges_proj.to_crs(epsg=3857)

# Assign colors for nodes: green=start, red=end, blue=others
nodes_proj["color"] = "blue"
if start_node in nodes_proj.index:
    nodes_proj.loc[start_node, "color"] = "green"
if end_node in nodes_proj.index:
    nodes_proj.loc[end_node, "color"] = "red"

# --- 12. Plot ---

fig, ax = plt.subplots(figsize=(12, 12))
edges_proj.plot(ax=ax, linewidth=1, edgecolor='black')
nodes_proj.plot(ax=ax, markersize=20, color=nodes_proj["color"], alpha=0.9)

# Add basemap
ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

ax.set_axis_off()
plt.title(f"Chinese Postman Route in Lake View, Chicago\nLength: {total_length_miles:.2f} miles", fontsize=15)
plt.show()