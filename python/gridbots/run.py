#!/usr/bin/env python3

"""
Script to launch gridbots.

Configures paths as needed to run the given simulation file and launches
Blenderplayer to render the simulation once complete.

"""

import os
import sys

from subprocess import call
from subprocess import check_output

# If gridbots not in python path, add it -
# This allows running this script directly
gb_pythonpath = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if gb_pythonpath not in sys.path:
    sys.path.append(gb_pythonpath)

import gridbots
from gridbots.core.simulation import Simulation


if __name__ == '__main__':

    try:
        sim_name = sys.argv[1]
    except IndexError:
        print('Usage: python -m gridbots.run [sim_name]')
        sys.exit(1)

    sim = Simulation(sim_name)
    paths_name = sim.run()

    # Get blenderplayer symbolic link (usually "/usr/local/bin/blenderplayer")
    bp_link = check_output(['which', 'blenderplayer'])[:-1]

    # Get absolute location of blenderplayer
    # (usually like "/usr/local/blender-2.70a-linux-glibc211-x86_64/blenderplayer")
    # For some reason, it throws an error when using a symlink
    bp_exec = check_output(['readlink', bp_link])[:-1]

    # Location of gridbots blender file
    gridbots_blend = os.path.join(gridbots.path, 'gridbots.blend')

    # Construct the required python path of the blenderplayer executable
    pythonpath = [s for s in sys.path if 'site-packages' in s]
    pythonpath.append(gb_pythonpath)
    os.environ['PYTHONPATH'] = ':'.join(pythonpath)

    # Execute blenderplayer
    call([bp_exec, "-m", "2", "-w", "800", "600", gridbots_blend, "-", paths_name],
         env=os.environ)
