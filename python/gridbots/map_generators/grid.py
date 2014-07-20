"""

"""

import sys
import yaml
from igraph import Graph, plot

if len(sys.argv) != 3:
    print('Usage: grid.py [width] [height]')
    sys.exit()

width = int(sys.argv[1])
height = int(sys.argv[2])

out = {}
out['vertices'] = {}
out['edges'] = []

for i in range(height):
    for j in range(width):

        v = i*width + j
        coords = [float(j), height-1-float(i)]

        out['vertices'][v] = coords

        if j > 0:
            out['edges'].append([v-1, v])

        if i > 0:
            out['edges'].append([v, v-width])

# g = Graph.Lattice([width, height], nei=1, circular=False)

# layout = g.layout()

# # p1 = g.vs[0]
# # p2 = g.vs[width-1]
# # print layout.coords

# # #layout.rotate(30)

# plot(g)

# for inx, v in enumerate(layout):
#     out['vertices'].append([inx, v])

# for e in g.es:
#     out['edges'].append([e.source, e.target])

print(yaml.dump(out))
