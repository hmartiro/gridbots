"""

"""

import networkx as nx


def get_node(x, y, z):

    nodes = []
    for n, d in G.nodes_iter(data=True):
        if d['x'] == x and d['y'] == y and d['z'] == z:
            nodes.append(n)
    return nodes


def shortest_path(p1, p2):

    n1 = get_node(*p1)[0]
    n2 = get_node(*p2)[0]

    return nx.shortest_path(G, n1, n2)

if __name__ == '__main__':
    import code

    map_name = 'stage'

    G = nx.read_gpickle('spec/maps/{}.gpickle'.format(map_name))

    print('Read map [{}]. Nodes: {}, Edges: {}'.format(map_name, G.number_of_nodes(), G.number_of_edges()))

    code.interact(
        banner='The map is loaded into the variable G. Explore!',
        local={'G': G, 'get_node': get_node, 'shortest_path': shortest_path}
    )
