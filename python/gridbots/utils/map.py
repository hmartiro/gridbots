"""

"""

import yaml

def read_map_as_graph(map_name):
    """
    Takes a map filename and returns a Graph 
    representing the contents of that map.

    """

    # Extract data from the map file
    vertices, edges = read_map(map_name)

    # Create a Graph object
    from igraph import Graph
    graph = Graph()

    graph.add_vertices(vertices.keys())

    for v in graph.vs:
        v["coords"] = vertices[v["name"]]

    for edge in edges:
        graph.add_edge(graph.vs.find(name=str(edge[0])), graph.vs.find(name=str(edge[1])))

    return graph

def read_map(map_name):
    """
    Takes a map filename and returns the edge
    and vertex data of the map.

    """
        # Read the map file
    map_filename = "maps/{}.yml".format(map_name)
    with open(map_filename) as map_file:
        map_data = yaml.load(map_file.read())

    # Extract data from the yaml
    vertices = map_data['vertices']
    edges = map_data['edges']

    return vertices, edges

def get_bounding_box(graph):
    """
    Given a map Graph, return the bounding box of
    the coordinates of the nodes in that map.

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
