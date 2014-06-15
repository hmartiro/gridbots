"""

"""

import yaml
import random


def read_graph(filename):
    """
    Takes a filename and returns a Graph 
    representing the contents of that file.

    """

    # Extract data from the map file
    vertices, edges = read_graph_data(filename)

    import networkx as nx
    # Create a Graph object
    graph = nx.Graph()

    # Add vertices
    for v in vertices:
        graph.add_node(v, coords=vertices[v])

    # Add edges
    for e in edges:
        graph.add_edge(e[0], e[1])

    return graph


def read_graph_data(filename):
    """
    Takes a filename and returns the edge
    and vertex data of the file.

    """
        # Read the map file
    with open(filename) as map_file:
        data = yaml.load(map_file.read())

    # Extract data from the yaml
    vertices = data['vertices']
    edges = data['edges']

    return vertices, edges


# def get_bounding_box(graph):
#     """
#     Given a Graph, return the bounding box of
#     the coordinates of the nodes.
#
#     """
#
#     min_x = min_y = float("+inf")
#     max_x = max_y = float("-inf")
#
#     for v in graph.vs:
#
#         x = v["coords"][0]
#         y = v["coords"][1]
#
#         if x > max_x:
#             max_x = x
#         if x < min_x:
#             min_x = x
#         if y > max_y:
#             max_y = y
#         if y < min_y:
#             min_y = y
#
#     return [min_x, max_x, min_y, max_y]


def find_shortest_path(graph, src, dest):
    """
    Given a graph, a source node, and a destination node,
    return an optimal path to the destination. If no path exists,
    returns None.

    """
    import networkx as nx
    # Get all the shortest paths
    try:
        all_paths = list(nx.all_shortest_paths(graph, src, dest))
    except nx.NetworkXNoPath:
        return None

    # Choose one at random
    random_index = random.randint(0, len(all_paths) - 1)
    return all_paths[random_index]
