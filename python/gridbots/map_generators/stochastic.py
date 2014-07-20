"""

"""

import sys
import yaml
from igraph import Graph, plot

if len(sys.argv) != 3:
    print('Usage: stochastic.py [nodes] [connectivity]')
    sys.exit()

nodes = int(sys.argv[1])
connectivity = float(sys.argv[2])

out = {}
out['vertices'] = {}
out['edges'] = []

g = Graph.GRG(nodes, connectivity)

plot(g)

for v in g.vs:
    out['vertices'][str(v.index)] = [v["x"], v["y"]]

for e in g.es:
    out['edges'].append([e.source, e.target])

print(yaml.dump(out))
