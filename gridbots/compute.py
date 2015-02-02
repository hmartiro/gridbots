#!/usr/bin/env python3
"""

"""

import os
import sys

# If gridbots not in python path, add it -
# This allows running this script directly
gb_pythonpath = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if gb_pythonpath not in sys.path:
    sys.path.append(gb_pythonpath)

from gridbots.core.simulation import Simulation


if __name__ == '__main__':

    try:
        sim_name = sys.argv[1]
    except IndexError:
        print('Usage: python -m gridbots.compute [sim_name]')
        sys.exit(1)

    sim = Simulation(sim_name)
    paths_name = sim.run()
