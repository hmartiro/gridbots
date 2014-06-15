import os
import sys

if __name__ != '__main__':
    sys.path.insert(0, '/usr/local/lib/python3.4/dist-packages')

from subprocess import call
from gridbots.core.simulation import Simulation

if __name__ == '__main__':

    sim = Simulation(sim_name=sys.argv[1])
    paths_name = sim.run()

    os.environ['PYTHONPATH'] = "/home/hayk/Projects/gridbots/python"
    blenderplayer_path = "/usr/local/blender-2.70a-linux-glibc211-x86_64/blenderplayer"
    call([blenderplayer_path, "-m", "2", "-w", "800", "600", "gridbots.blend", "-", paths_name], env=os.environ)

renderer = None


def set_renderer(r):
    global renderer
    renderer = r


def get_renderer():
    return renderer


def start_rendering():

    from gridbots.renderers.blender import BlenderDrawer
    
    if len(sys.argv) >= 9:
        paths_name = sys.argv[8]
    else:
        paths_name = 'paths_two_cross'

    renderer = BlenderDrawer(paths_name=paths_name)
    set_renderer(renderer)


def render_frame():
    
    renderer.update()
