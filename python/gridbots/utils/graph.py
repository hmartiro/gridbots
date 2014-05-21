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

    # Create a Graph object
    from igraph import Graph
    graph = Graph()

    graph.add_vertices(vertices.keys())

    for v in graph.vs:
        v["coords"] = vertices[v["name"]]

    for edge in edges:
        graph.add_edge(graph.vs.find(name=edge[0]), graph.vs.find(name=edge[1]))

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


def get_bounding_box(graph):
    """
    Given a Graph, return the bounding box of
    the coordinates of the nodes.

    """

    min_x = min_y = float("+inf")
    max_x = max_y = float("-inf")

    for v in graph.vs:

        x = v["coords"][0]
        y = v["coords"][1]

        if x > max_x:
            max_x = x
        if x < min_x:
            min_x = x
        if y > max_y:
            max_y = y
        if y < min_y:
            min_y = y
    
    return [min_x, max_x, min_y, max_y]


def find_shortest_path(graph, src, dest):
    """
    Given a graph, a source node, and a destination node,
    return an optimal path to the destination. If no path exists,
    returns None.

    """
    n_src = graph.vs.find(name=src)
    n_target = graph.vs.find(name=dest)

    # Get all the shortest paths
    all_path_ids = graph.get_shortest_paths(n_src, to=n_target)

    # If there is no path, return None
    if len(all_path_ids) == 0:
        return None

    # Choose one at random
    random_index = random.randint(0, len(all_path_ids) - 1)
    random_path_ids = all_path_ids[random_index]

    # Convert IDs to vertex names
    moves = [graph.vs[m]["name"] for m in random_path_ids]

    return moves


def get_neighbors(graph, node):

    return [n["name"] for n in graph.vs.find(name=node).neighbors()]
