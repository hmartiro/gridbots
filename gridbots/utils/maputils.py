"""

"""

import networkx as nx
from operator import itemgetter

ERROR_TOLERANCE = 1e-4


def _get_node(x, y, z):

    nodes = []
    for n, d in G.nodes_iter(data=True):

        if abs(d['x'] - x) + abs(d['y'] - y) + abs(d['z'] - z) < ERROR_TOLERANCE:
            nodes.append(n)

    return nodes


def node_from_pos(x, y, z=0):
    """
    Given an XYZposition in mm, returns the name of the corresponding node at
    this point. If there are no nodes, returns None. If there are multiple,
    throws an exception.
    """
    nodes = _get_node(x/24., y/24., z)

    if len(nodes) == 1:
        return nodes[0]
    elif len(nodes) == 0:
        return None
    else:
        raise Exception('Multiple nodes at ({}, {}): {}'.format(x, y, nodes))


def pos_from_node(node):
    """
    Given a node ID, return the node's x and y position in millimeters.
    """
    return G.node[node]['x']*24, G.node[node]['y']*24


def shortest_path(p1, p2):

    n1 = _get_node(*p1)[0]
    n2 = _get_node(*p2)[0]

    return nx.shortest_path(G, n1, n2)

if __name__ == '__main__':
    import code

    map_name = 'stage'

    G = nx.read_gpickle('spec/maps/{}.gpickle'.format(map_name))

    print('Read map [{}]. Nodes: {}, Edges: {}'.format(map_name, G.number_of_nodes(), G.number_of_edges()))

    code.interact(
        banner='The map is loaded into the variable G. Explore!',
        local={
            'G': G,
            'node_from_pos': node_from_pos,
            'pos_from_node': pos_from_node,
            'shortest_path': shortest_path
        }
    )
