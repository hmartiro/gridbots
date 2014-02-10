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

"""

from gridbots.core.bot import Bot, Orientation
from gridbots.core.simulation import Simulation

from gridbots.renderers.pygame2d import PyGameDrawer

if __name__ == '__main__':

    a = Bot(x=-3, y=-5, orientation=Orientation.N)
    b = Bot(x=0, y=0, orientation=Orientation.W)

    moves = (
                (
                    (0,1),
                    (1,1),
                    (1,1),
                    (1,1),
                    (1,1),
                    (1,1),
                    (1,1),
                    (1,1),
                    (1,1)
                ), 
                (
                    (-1,0),
                    (1,-1),
                    (1,1),
                    (1,1),
                    (1,1),
                    (1,1),
                    (1,1),
                    (1,1),
                    (1,1)
                )
            )

    sim = Simulation(bots=[a, b], moves=moves, renderer=PyGameDrawer)

    sim.run()
