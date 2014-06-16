"""

"""

import os
import sys

from subprocess import call
from subprocess import check_output

import gridbots
from gridbots.core.simulation import Simulation

if __name__ == '__main__':

    sim = Simulation(sim_name=sys.argv[1])
    paths_name = sim.run()

    # Get blenderplayer symbolic link (usually "/usr/local/bin/blenderplayer")
    bp_link = check_output(['which', 'blenderplayer'])[:-1]

    # Get absolute location of blenderplayer
    # (usually like "/usr/local/blender-2.70a-linux-glibc211-x86_64/blenderplayer")
    # For some reason, it throws an error when using a symlink
    bp_exec = check_output(['readlink', bp_link])[:-1]

    # Construct the required python path of the blenderplayer executable
    gridbots_dir = os.path.dirname(os.path.dirname(os.path.realpath(gridbots.__file__)))
    site_packages_dir = '/home/hayk/.virtualenvs/gridbots3/lib/python3.4/site-packages/'
    os.environ['PYTHONPATH'] = "{}:{}".format(gridbots_dir, site_packages_dir)

    # Execute blenderplayer
    call([bp_exec, "-m", "2", "-w", "800", "600", "gridbots.blend", "-", paths_name], env=os.environ)
