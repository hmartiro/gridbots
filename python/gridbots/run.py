import sys

from gridbots.core.simulation import Simulation
from gridbots.renderers.pygame2d import PyGameDrawer

if __name__ == '__main__':

    sim = Simulation(sim_name=sys.argv[1])
    paths_name = sim.run()

    renderer = PyGameDrawer(paths_name=paths_name)
    renderer.run()
