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
    # print('v1: {}, v2: {}'.format(v1, v2))

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
        edges_to_add.append((source_id, dest_id, {zone.name: labels[0]}))
        edges_to_add.append((dest_id, source_id, {zone.name: labels[1]}))

    g.add_edges_from(edges_to_add)


def parse_rotational_pixel(g, zone, pixel):
    """
    Add the given rotational pixel to the graph.
    """

    add_all_pixel_nodes(g, zone, pixel)

    edges_to_add = []
    for e in pixel.data.edges:

        v1 = pixel.data.vertices[e.vertices[0]].co
        v2 = pixel.data.vertices[e.vertices[1]].co

        labels = check_direction_xy(v1, v2)

        # Skip side edges of rotational pixels
        if labels is not None:
            continue

        if v1.x - v1.y > v2.x - v2.y:
            labels = ('-X', '+X')
        else:
            labels = ('+X', '-X')

        source_id = '{}.{}.{}'.format(zone.name, pixel.name, e.vertices[0])
        dest_id = '{}.{}.{}'.format(zone.name, pixel.name, e.vertices[1])
        edges_to_add.append((source_id, dest_id, {zone.name: labels[0]}))
        edges_to_add.append((dest_id, source_id, {zone.name: labels[1]}))

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
        edges_to_add.append((source_id, dest_id, {zone.name: labels[0]}))
        edges_to_add.append((dest_id, source_id, {zone.name: labels[1]}))

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

    # Define equality as all three coordinates being (almost) equal
    MERGE_THRESHOLD = 1e-3

    def eq(u, v):
        return (
            abs(u[1] - v[1]) < MERGE_THRESHOLD and
            abs(u[2] - v[2]) < MERGE_THRESHOLD and
            abs(u[3] - v[3]) < MERGE_THRESHOLD
        )

    print('Nodes and edges before merging edges: {}, {}'.format(g.number_of_nodes(), g.number_of_edges()))

    # Map of nodes being replaced to their replacement
    replacements = {}

    # Loop through looking for co-located vertices
    edges_to_add = []
    for i in range(len(v_list) - 1):

        if eq(v_list[i], v_list[i+1]):

            n1 = v_list[i][0]
            n2 = v_list[i+1][0]

            # Mark node for merge
            replacements[n2] = n1

            for n2d, n, data in g.out_edges(n2, data=True):
                assert(n2d == n2)
                edges_to_add.append((n1, n, data))

            for n, n2d, data in g.in_edges(n2, data=True):
                assert(n2d == n2)
                edges_to_add.append((n, n1, data))

    def bad_ref_count(edge_list):
        bad_ref = 0
        for n1, n2, data in edges_to_add:
            if n1 in replacements:
                bad_ref += 1
            if n2 in replacements:
                bad_ref += 1
        return bad_ref

    def replace(e):
        n1 = replacements.get(e[0], e[0])
        n2 = replacements.get(e[1], e[1])
        data = e[2]
        return n1, n2, data

    while bad_ref_count(edges_to_add) > 0:
        edges_to_add = list(map(replace, edges_to_add))

    print('Total duplicates: {}'.format(len(replacements)))
    print('Nodes and edges before: {}, {}'.format(g.number_of_nodes(), g.number_of_edges()))
    g.remove_nodes_from(replacements.keys())
    print('Nodes and edges after removing dupes: {}, {}'.format(g.number_of_nodes(), g.number_of_edges()))

    for e in edges_to_add:
        if g.has_edge(e[0], e[1]):
            old_data = g[e[0]][e[1]]
            e[2].update(old_data)
        g.add_edge(*e)

    print('Nodes and edges after adding edges: {}, {}'.format(g.number_of_nodes(), g.number_of_edges()))
    print('Total edges moved during merge: {}'.format(len(edges_to_add)))


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

        name = sys.argv[4][:-6]

        nx.write_gpickle(G, 'spec/maps/{}.gpickle'.format(name))

        from mathutils import Vector

        scn = bpy.context.scene

        # Delete all other objects
        for ob in scn.objects:
            ob.select = True
        bpy.ops.object.delete()

        # Create mesh and object
        me = bpy.data.meshes.new('{}_mesh'.format(name))
        ob = bpy.data.objects.new(name, me)
        ob.location = Vector((0, 0, 0))
        ob.show_name = True

        # Link object to scene and make active
        scn.objects.link(ob)
        scn.objects.active = ob
        ob.select = True

        # Generate mesh vertices and edges
        G2 = nx.convert_node_labels_to_integers(G)
        verts = [(v[1]['x'], v[1]['y'], v[1]['z']) for v in G2.nodes_iter(data=True)]
        edges = G2.edges()
        faces = []

        # Fill in mesh data
        me.from_pydata(verts, edges, faces)
        me.update()

        # Save the .blend file
        bpy.ops.wm.save_as_mainfile(filepath='{}-generated.blend'.format(name))

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
