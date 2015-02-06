"""

"""

import sys
import math
import numpy as np
from pprint import pformat
import logging

logger = logging.getLogger(__name__)

from gridbots.generators.structure.ply_to_graph import ply_to_graph

PRECISION = 4
ERROR = 1e-4


def fill_hollow_box_mesh(verts, edges):

    # Find the minimum X, Y, Z coordinates
    min_point = [0, 0, 0]
    for v in verts.values():
        if v[0] < min_point[0]:
            min_point[0] = v[0]
        if v[1] < min_point[1]:
            min_point[1] = v[1]
        if v[2] < min_point[2]:
            min_point[2] = v[2]

    # Offset all so min point is (0, 0, 0)
    for v_id in verts:
        verts[v_id] = [verts[v_id][i] - min_point[i] for i, _ in enumerate(min_point)]

    # Find the average edge length
    lengths = [np.linalg.norm(np.array(verts[u]) - np.array(verts[v])) for u, v in edges]
    avg_len = np.mean(lengths)
    logger.debug('avg length: {}'.format(avg_len))
    stddev = np.std(lengths)
    logger.debug('std dev of length: {}'.format(stddev))
    greatest_deviation = max([np.linalg.norm(l - avg_len) for l in lengths])
    logger.debug('greatest edge deviation from mean: {}'.format(greatest_deviation))

    # Scale all so the average length is 1
    for v_id in verts:
        verts[v_id] = [v / avg_len for v in verts[v_id]]

    # Round to precision to avoid small errors
    for v_id, vert in verts.items():
        verts[v_id] = [float(round(v, PRECISION)) for v in vert]

    # Separate out trees, verticals, and horizontals
    def is_x_rod(e):
        v1 = verts[e[0]]
        v2 = verts[e[1]]
        return (v1[1] - v2[1] == 0) and (v1[2] - v2[2] == 0)

    def is_z_rod(e):
        v1 = verts[e[0]]
        v2 = verts[e[1]]
        return (v1[0] - v2[0] == 0) and (v1[1] - v2[1] == 0)

    def is_y_rod(e):
        v1 = verts[e[0]]
        v2 = verts[e[1]]
        return (v1[0] - v2[0] == 0) and (v1[2] - v2[2] == 0)

    x_rods = list(filter(is_x_rod, edges))
    y_rods = list(filter(is_y_rod, edges))
    z_rods = list(filter(is_z_rod, edges))

    # Fill in the hollow spots with regulary placed rods
    x_rods = fill_in_mesh(verts, x_rods, 0)
    y_rods = fill_in_mesh(verts, y_rods, 1)
    z_rods = fill_in_mesh(verts, z_rods, 2)

    edges = x_rods + y_rods + z_rods

    # Sort edges by y, z, then x coordinates, ascending
    sort_edges(verts, edges, 1)  # y
    sort_edges(verts, edges, 2)  # z
    sort_edges(verts, edges, 0)  # x

    # Finally sort, preserving X order, to put verticals before
    # horizontals
    def type_sort(e):
        v1 = verts[e[0]]
        v2 = verts[e[1]]
        x_max = -max(v1[0], v2[0])
        x_min = -min(v1[0], v2[0])
        return x_max, x_min, v1[2] == v2[2]

    edges.sort(key=type_sort)

    # The edges are now in the correct order to be built, aside
    # from tree/vertical/horizontal build order
    logger.debug('------ Final output ------')
    print_output(verts, edges)

    return verts, edges


def sort_edges(verts, edges, axis):
    edges.sort(key=lambda e: -min(verts[e[0]][axis], verts[e[1]][axis]))
    edges.sort(key=lambda e: -max(verts[e[0]][axis], verts[e[1]][axis]))


def fill_in_mesh(verts, edges, axis):
    """
    Fill in the given edges along the specified axis. Algorithm is to

    """
    # Make edges always point towards the more positive node
    for i, e in enumerate(edges):
        v1 = verts[e[0]]
        v2 = verts[e[1]]
        if v1[axis] > v2[axis]:
            edges[i] = [e[1], e[0]]

    # Sort by other two directions first, then along the edge axis
    axis1 = (axis + 1) % 3
    axis2 = (axis + 2) % 3
    sort_edges(verts, edges, axis1)
    sort_edges(verts, edges, axis2)
    sort_edges(verts, edges, axis)
    edges.reverse()

    def get_verts(_):
        return verts[edges[_][0]], verts[edges[_][1]]

    filled_edges = list(edges)

    #print_output(verts, edges)

    fill_vert_id = 0

    # ------------------------------
    # Fill along one axis
    fill_axis = axis1
    other_axis = axis2

    inx = 0
    while inx < len(edges):

        v, _ = get_verts(inx)
        v = list(v)

        logger.debug('\n>>> Rods along axis {}, filling along axis {}, starting with {}'.format(
            axis, fill_axis, v
        ))

        inx += 1
        while inx < len(edges):

            v1, _ = get_verts(inx)

            if (v[other_axis] != v1[other_axis]) or (v[axis] != v1[axis]):
                break

            logger.debug('Checking for gap between {} and {}'.format(v, v1))

            fill_axis_gap = v1[fill_axis] - v[fill_axis]

            if fill_axis_gap == 1:
                logger.debug('No gap, moving on.')
            elif fill_axis_gap > 1:
                num_fill = int(round(fill_axis_gap)) - 1
                logger.debug('Filling in gap with {} extra edges.'.format(num_fill))
                for i in range(num_fill):

                    v_new = [0, 0, 0]
                    v_new[axis] = v[axis]
                    v_new[other_axis] = v[other_axis]
                    v_new[fill_axis] = v[fill_axis] + i + 1
                    v_new_id = 'f_{}_{}'.format(axis, fill_vert_id)
                    fill_vert_id += 1
                    verts[v_new_id] = v_new

                    v_new2 = list(v_new)
                    v_new2[axis] += 1
                    v_new2_id = 'f_{}_{}'.format(axis, fill_vert_id)
                    fill_vert_id += 1
                    verts[v_new2_id] = v_new2

                    filled_edges.append([v_new_id, v_new2_id])

                    logger.debug('Added edge {} at offset {} from {}'.format(v_new, i + 1, v))
            else:
                raise Exception('Gap between edges is less than one: {}'.format(fill_axis_gap))

            v = v1
            inx += 1

    # Sort again for good formatting
    sort_edges(verts, filled_edges, axis1)
    sort_edges(verts, filled_edges, axis2)
    sort_edges(verts, filled_edges, axis)
    filled_edges.reverse()

    #print_output(verts, filled_edges)

    return filled_edges


def print_output(verts, edges):

    logger.debug('-----------------------------')
    output = ['{} -> {}'.format(
        *['({}) {}'.format(v_id, verts[v_id]) for v_id in edge]
    ) for edge in edges]

    logger.debug('\n'.join(output))


#def get_rods_in_build_order

if __name__ == '__main__':

    f = sys.argv[1]
    filled_vs, filled_es = fill_hollow_box_mesh(*ply_to_graph(f))

    print_output(filled_vs, filled_es)

    data = {'vertices': filled_vs, 'edges': filled_es}

    import yaml
    logger.debug(yaml.dump(data))
