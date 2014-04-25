import sys

from gridbots.core.simulation import Simulation
from gridbots.renderers.pygame2d import PyGameDrawer

if __name__ == '__main__':

    sim = Simulation(map_filename='maps/{}.yml'.format(sys.argv[1]), renderer=PyGameDrawer)
    sim.run()
