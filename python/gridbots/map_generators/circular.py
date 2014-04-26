"""

"""

import sys
import yaml
from igraph import Graph, plot

if len(sys.argv) != 3:
    print('Usage: grid.py [slices] [depth]')
    sys.exit()

width = int(sys.argv[1])
height = int(sys.argv[2])

out = {}
out['vertices'] = []
out['edges'] = []

g = Graph.Lattice([width, height], circular=True)

plot(g)

layout = g.layout()

for inx, v in enumerate(layout):
    out['vertices'].append([inx, v])

for e in g.es:
    out['edges'].append([e.source, e.target])

print yaml.dump(out)
