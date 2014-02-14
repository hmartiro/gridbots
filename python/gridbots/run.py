"""

Gridbots plan:

Inputs:
- File describing the terrain 
    - This should be represented as a graph data structure
- File describing the initial positions
- File describing the goal positions

Outputs:
- Paths of each robot
- Visualization

Stages of abstraction:
- robot positions at timesteps
- object positions at timesteps, robot paths generated
- final object structure, object positions and robot paths generated

Todo:
- Multi-robot avoidance
- Permanent obstacle capability
- Tasks (get resources, place into structure)
- End effectors
  - input of 
  - rotation points
  - rendering
- Goal generation based on paths
- Blender!

"""

import sys

from gridbots.core.simulation import Simulation
from gridbots.renderers.pygame2d import PyGameDrawer

if __name__ == '__main__':

    sim = Simulation(map_filename='maps/{}.yml'.format(sys.argv[1]), renderer=PyGameDrawer)

    sim.run()
