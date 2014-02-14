"""

"""

import sys
import yaml

if len(sys.argv) != 4:
    print('Usage: map_generator.py [name] [width] [height]')
    sys.exit()

name = sys.argv[1]
width = int(sys.argv[2])
height = int(sys.argv[3])

out = {}
out['name'] = name
out['vertices'] = []
out['edges'] = []
out['bots'] = {}

for i in range(height):
    for j in range(width):

        v = i*width + j
        coords = [float(j), float(i)]

        out['vertices'].append([v, coords])

        if j > 0:
            out['edges'].append([v-1, v])

        if i > 0:
            out['edges'].append([v, v-width])

print yaml.dump(out)
