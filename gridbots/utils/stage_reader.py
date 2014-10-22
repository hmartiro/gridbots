"""

"""

import os
import sys
from pprint import pprint
import subprocess


def check_direction(v1, v2):

        error = 0.0001

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


def parse_flex_pixel(pixel):

    out = dict()

    out['vertices'] = dict()
    out['edges'] = dict()

    for v in pixel.data.vertices:
        out['vertices'][str(v.index)] = [round(c, 6) for c in v.co]

    for e in pixel.data.edges:
        out['edges'][str(e.index)] = list(e.vertices)

    return out


def parse_rotational_pixel(pixel):

    out = dict()

    out['vertices'] = dict()
    out['edges'] = dict()

    for v in pixel.data.vertices:
        out['vertices'][str(v.index)] = [round(c, 6) for c in v.co]

    for e in pixel.data.edges:
        out['edges'][str(e.index)] = list(e.vertices)

    return out


def parse_regular_pixel(pixel):

    out = dict()

    out['vertices'] = dict()
    out['edges'] = dict()

    for v in pixel.data.vertices:
        out['vertices'][v.index] = dict()
        out['vertices'][v.index]['pos'] = [round(c, 6) for c in v.co]
        out['vertices'][v.index]['edges'] = {}

    for e in pixel.data.edges:

        verts = list(e.vertices)
        source = pixel.data.vertices[verts[0]].co
        dest = pixel.data.vertices[verts[1]].co

        labels = check_direction(source, dest)

        if labels is None:
            raise IOError('Bad edge!')

        out['vertices'][verts[0]]['edges'][labels[0]] = verts[1]
        out['vertices'][verts[1]]['edges'][labels[1]] = verts[0]

        out['edges'][e.index] = list(e.vertices)

    if pixel.name == 'Gridblock.004':
        pprint(out)

    return out


def parse_zone(zone):

    out = dict()

    for pixel in zone.objects:

        if 'Gridblock' in pixel.name:
            s = parse_regular_pixel(pixel)
        elif 'Rotate' in pixel.name:
            s = parse_rotational_pixel(pixel)
        elif 'Flex' in pixel.name:
            s = parse_flex_pixel(pixel)
        else:
            raise IOError('Pixel type {} not understood!'.format(pixel.name))

        out[pixel.name] = s

    return out


def parse_all():

    out = dict()

    for zone in bpy.data.groups:
        out[zone.name] = parse_zone(zone)

    return out


if __name__ == '__main__':

    if 'blender' in sys.argv[0]:

        sys.path.append(os.path.dirname(sys.argv[-1]))

        import bpy

        output = parse_all()

        import pickle
        import zlib

        s = zlib.compress(pickle.dumps(output))
        with open('stage.map', 'wb') as f:
            f.write(s)

    else:

        subprocess.check_call([
            'blender',
            '--background',
            './stage.blend',
            '--python',
            'utils/stage_reader.py',
            '--'
        ])
