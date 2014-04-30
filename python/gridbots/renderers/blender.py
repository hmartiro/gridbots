"""

"""

import math

FRAMERATE = 3
REDRAW_SUBSTEPS = 10

###############################

def linmap(val, inMin, inMax, outMin, outMax):
    """
    Simple linear mapping utility.
    """
    return (val-inMin)/(inMax-inMin) * (outMax-outMin) + outMin

###############################

class BlenderDrawer():

    def __init__(self, sim, framerate=FRAMERATE, substeps=REDRAW_SUBSTEPS):

        # Reference to the simulation object
        self.sim = sim


        self.framerate = framerate
        self.substeps = substeps

        # Get map dimensions
        self.minX = self.sim.map_dimensions[0]
        self.maxX = self.sim.map_dimensions[1]
        self.minY = self.sim.map_dimensions[2] 
        self.maxY = self.sim.map_dimensions[3]

        self.scaling = math.sqrt((self.maxY - self.minY) * (self.maxX - self.minX))

        self.t = 0

    def setup(self):

        import bge

        # Top-level BGE objects
        cont = bge.logic.getCurrentController()
        scene = bge.logic.getCurrentScene()

    def update(self):

        self.t += 1
        print(t)

    def run(self):
        pass
