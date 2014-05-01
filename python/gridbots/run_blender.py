import os
import sys

from subprocess import call

from gridbots.core.simulation import Simulation

if __name__ == '__main__':

    sim = Simulation(sim_name=sys.argv[1])
    paths_name = sim.run()

    call(["blenderplayer", "gridbots.blend", "-", paths_name])

renderer = None
def set_renderer(r):
    global renderer
    renderer = r
def get_renderer():
    return renderer

def start_rendering():

    from gridbots.renderers.blender import BlenderDrawer
    
    #sys.path.append('/usr/local/lib/python3.3/dist-packages')
    #sys.path.append('/usr/lib/python3/dist-packages')
    
    if len(sys.argv) >= 4:
        paths_name = sys.argv[3]
    else:
        paths_name = 'paths_two_cross'

    renderer = BlenderDrawer(paths_name=paths_name)
    set_renderer(renderer)

def render_frame():
    
    renderer.update()
