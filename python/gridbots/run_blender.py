import sys

from gridbots.core.simulation import Simulation
from gridbots.renderers.blender import BlenderDrawer

from subprocess import call

simulation = 'four_cross'

sim = Simulation(simulation_file='simulations/{}.yml'.format(simulation), renderer=BlenderDrawer)

def main():

    sim.run()

    print(call(["blenderplayer", "gridbots.blend"]))

def update():
    sim.renderer.update()

main()
