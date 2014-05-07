"""

"""

import math
import yaml
import time

from gridbots.utils.graph import read_graph_data
from gridbots.utils.graph import get_bounding_box

import bge

# Must match that of the BGE!! (fps)
BLENDER_FPS = 40

# Desired framerate of simulation (fps)
FRAMERATE = 5

###############################

def linmap(val, inMin, inMax, outMin, outMax):
    """
    Simple linear mapping utility.
    """
    return (val-inMin)/(inMax-inMin) * (outMax-outMin) + outMin

###############################

class BlenderDrawer():

    def __init__(self, paths_name, framerate=FRAMERATE):

        # Read the paths file
        paths_file ='paths/{}.yml'.format(paths_name)
        with open(paths_file) as pf:
            paths_data = yaml.load(pf.read())

        # Get map data
        self.vertices, self.edges = read_graph_data("maps/{}.yml".format(paths_data["map_name"]))

        self.framerate = framerate
        self.substeps = int(float(BLENDER_FPS) / float(self.framerate))

        self.bot_data = paths_data["bots"]

        self.frames = paths_data["frames"]

        # Get map dimensions
        #self.bounding_box = get_bounding_box(self.graph)
        #self.minX = self.bounding_box[0]
        #self.maxX = self.bounding_box[1]
        #self.minY = self.bounding_box[2] 
        #self.maxY = self.bounding_box[3]

        #self.scaling = math.sqrt((self.maxY - self.minY) * (self.maxX - self.minX))
        
        # Top-level BGE objects
        self.C = bge.logic.getCurrentController()
        self.S = bge.logic.getCurrentScene()

        # Which simulation frame are we on?
        self.frame = 0

        # Which substep of the simulation frame?
        self.substep = 0

        self.bots = {}
        for bot in self.bot_data.keys():
            self.bots[bot] = self.S.addObject('Robot', self.C.owner)

        # Draw nodes
        self.nodes = {}
        for name, coords in self.vertices.items():
            self.nodes[name] = self.S.addObject('Node', self.C.owner)
            self.nodes[name].position = (coords[0], coords[1], 0.)

    def update(self):

        if(self.frame > self.frames - 1):
            return

        print('------- frame {} -------'.format(self.frame))

        for bot_name, bot in self.bots.items():
            
            node1 = self.bot_data[bot_name][self.frame]
            node2 = self.bot_data[bot_name][self.frame+1]

            c1 = self.vertices[node1]
            c2 = self.vertices[node2]

            fraction = self.substep / float(self.substeps)

            x = c1[0] * (1-fraction) + c2[0] * fraction
            y = c1[1] * (1-fraction) + c2[1] * fraction

            bot.position = (x, y, 0.)

        self.substep += 1

        if(self.substep == self.substeps):
            self.substep = 0
            self.frame += 1
