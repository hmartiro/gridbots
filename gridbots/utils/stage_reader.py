"""

"""

import os
import sys
import subprocess
from operator import itemgetter

error = 0.0001


def check_direction_xy(v1, v2):
    """
    Return +/- X/Y pairs depending on the direction vector between
    the given two coordinates, ignoring the z values. Tolerate a
    small amount of error. Return None if not along the X or Y axes.
    """

    v = (v2 - v1).normalized()

    if abs(v.x) > error:

        if abs(v.y) > error:
            return None

        return ('+X', '-X') if v.x > 0 else ('-X', '+X')

    elif abs(v.y) > error:

        if abs(v.x) > error:
            return None

        return ('+Y', '-Y') if v.y > 0 else ('-Y', '+Y')

    return None


def check_direction_orthogonal(v1, v2):
    """
    Return +/- X/Y/Z pairs depending on the direction vector between
    the given two coordinates. Tolerate a small amound of error. Return
    None if not one of the orthogonal directions.

    """

    v = (v2 - v1).normalized()

    if abs(v.x) > error:

        if abs(v.y) + abs(v.z) > error:
            return None

        return ('+X', '-X') if v.x > 0 else ('-X', '+X')

    elif abs(v.y) > error:

        if abs(v.x) + abs(v.z) > error:
            return None

        return ('+Y', '-Y') if v.y > 0 else ('-Y', '+Y')

    elif abs(v.z) > error:

        if abs(v.x) + abs(v.y) > error:
            return None

        return ('+Z', '-Z') if v.z > 0 else ('-Z', '+Z')

    return None


def add_all_pixel_nodes(g, zone, pixel):

    nodes_to_add = []
    for v in pixel.data.vertices:

        # Add the vertex's location within the pixel to the pixel's location
        x, y, z = [round(c + bc, 6) for c, bc in zip(v.co, pixel.location)]

        # Make a unique name for the pixel
        node_id = '{}.{}.{}'.format(zone.name, pixel.name, v.index)

        # Add to the graph
        nodes_to_add.append((node_id, {
            'x': x,
            'y': y,
            'z': z
        }))

    g.add_nodes_from(nodes_to_add, zone=zone['number'], pixel=pixel.name)


def parse_flex_pixel(g, zone, pixel):
    """
    Add the given flex pixel to the graph.
    """

    add_all_pixel_nodes(g, zone, pixel)

    edges_to_add = []
    for e in pixel.data.edges:

        labels = check_direction_xy(
            pixel.data.vertices[e.vertices[0]].co,
            pixel.data.vertices[e.vertices[1]].co
        )

        if labels is None:
            raise IOError('Bad edge!')

        # Skip Y edges - flex pixels only have X direction
        if labels[0] == '+Y' or labels[0] == '-Y':
            continue

        source_id = '{}.{}.{}'.format(zone.name, pixel.name, e.vertices[0])
        dest_id = '{}.{}.{}'.format(zone.name, pixel.name, e.vertices[1])
        edges_to_add.append((source_id, dest_id, {'group': labels[0]}))
        edges_to_add.append((dest_id, source_id, {'group': labels[1]}))

    g.add_edges_from(edges_to_add)


def parse_rotational_pixel(g, zone, pixel):
    """
    Add the given rotational pixel to the graph.
    """

    add_all_pixel_nodes(g, zone, pixel)

    edges_to_add = []
    for e in pixel.data.edges:

        labels = check_direction_xy(
            pixel.data.vertices[e.vertices[0]].co,
            pixel.data.vertices[e.vertices[1]].co
        )

        if labels is not None:
            continue

        labels = ('+X', '-X')

        source_id = '{}.{}.{}'.format(zone.name, pixel.name, e.vertices[0])
        dest_id = '{}.{}.{}'.format(zone.name, pixel.name, e.vertices[1])
        edges_to_add.append((source_id, dest_id, {'group': labels[0]}))
        edges_to_add.append((dest_id, source_id, {'group': labels[1]}))

    g.add_edges_from(edges_to_add)


def parse_regular_pixel(g, zone, pixel):
    """
    Add the given regular pixel to the graph.
    """

    add_all_pixel_nodes(g, zone, pixel)

    edges_to_add = []
    for e in pixel.data.edges:

        labels = check_direction_orthogonal(
            pixel.data.vertices[e.vertices[0]].co,
            pixel.data.vertices[e.vertices[1]].co
        )

        if labels is None:
            raise IOError('Bad edge!')

        source_id = '{}.{}.{}'.format(zone.name, pixel.name, e.vertices[0])
        dest_id = '{}.{}.{}'.format(zone.name, pixel.name, e.vertices[1])
        edges_to_add.append((source_id, dest_id, {'group': labels[0]}))
        edges_to_add.append((dest_id, source_id, {'group': labels[1]}))

    g.add_edges_from(edges_to_add)


def parse_zone(g, zone):
    """
    Add the given zone to the graph.
    """

    zone['number'] = int(zone.name[1:])

    last_node_count, last_edge_count = g.number_of_nodes(), g.number_of_edges()

    for pixel in zone.objects:

        if pixel.name.startswith('P.'):
            parse_regular_pixel(g, zone, pixel)
        elif pixel.name.startswith('PR.'):
            parse_rotational_pixel(g, zone, pixel)
        elif pixel.name.startswith('PF.'):
            parse_flex_pixel(g, zone, pixel)
        else:
            raise IOError('Pixel type {} not understood!'.format(pixel.name))

        node_count, edge_count = g.number_of_nodes(), g.number_of_edges()
        print('pixel: {}, new n: {}, new e: {}, tot n: {}, tot e: {}'.format(
            pixel.name,
            node_count - last_node_count,
            edge_count - last_edge_count,
            node_count,
            edge_count
        ))
        last_node_count, last_edge_count = node_count, edge_count


def merge_vertices(g):
    """
    Merge together duplicate (co-located) vertices by moving all edges into
    the first node and removing the second node.

    """

    # Sort vertices by x, y, z coordinates
    v_list = [(n, d['x'], d['y'], d['z']) for n, d in g.nodes_iter(data=True)]

    v_list.sort(key=itemgetter(1, 2, 3, 0))

    # Define equality as all three coordinates being equal
    def eq(u, v):
        return (u[1] == v[1]) and (u[2] == v[2]) and (u[3] == v[3])

    print('Nodes and edges before merging edges: {}, {}'.format(g.number_of_nodes(), g.number_of_edges()))

    # Loop through looking for co-located vertices
    dupes_to_remove = []
    for i in range(len(v_list) - 1):

        if eq(v_list[i], v_list[i+1]):

            n1 = v_list[i][0]
            n2 = v_list[i+1][0]

            # Mark node for removal
            dupes_to_remove.append(n2)

            # Add edges of node 2 to node 1
            for n in g[n2].keys():
                g.add_edge(n1, n, g[n2][n])

    print('Total duplicates: {}'.format(len(dupes_to_remove)))
    print('Nodes and edges after merging edges: {}, {}'.format(g.number_of_nodes(), g.number_of_edges()))
    g.remove_nodes_from(dupes_to_remove)
    print('Nodes and edges after removing dupes: {}, {}'.format(g.number_of_nodes(), g.number_of_edges()))


def parse_all():
    """
    Return a graph representing map in the the .blend file.
    """

    g = nx.DiGraph(name=' '.join(sys.argv))

    # Create all edges and vertices
    for zone in bpy.data.groups:
        parse_zone(g, zone)

    # Merge vertices
    merge_vertices(g)

    return g


if __name__ == '__main__':

    if 'blender' in sys.argv[0]:

        sys.path.append(os.path.dirname(sys.argv[-1]))

        import bpy
        import networkx as nx

        G = parse_all()

        nx.write_gpickle(G, 'stage.gpickle')
    else:

        import networkx

        subprocess.check_call([
            'blender',
            '--background',
            sys.argv[1],
            '--python',
            sys.argv[0],
            '--',
            networkx.__path__[0]
        ])
