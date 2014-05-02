"""

"""

import math
import yaml

from gridbots.utils.map import read_map
from gridbots.utils.map import get_bounding_box

import bge

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

    def __init__(self, paths_name, framerate=FRAMERATE, substeps=REDRAW_SUBSTEPS):

        # Read the paths file
        paths_file ='paths/{}.yml'.format(paths_name)
        with open(paths_file) as pf:
            paths_data = yaml.load(pf.read())

        # Get map data
        self.vertices, self.edges = read_map(paths_data["map_name"])

        self.framerate = framerate
        self.substeps = substeps

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

        self.frame = 0

        self.bots = {}
        for bot in self.bot_data.keys():
            self.bots[bot] = self.S.addObject('Robot', self.C.owner)

    def update(self):

        if(self.frame > self.frames - 1):
            return

        print('------- frame {} -------'.format(self.frame))

        print(self.S.objects)

        for bot_name, bot in self.bots.items():
            
            node1 = self.bot_data[bot_name][self.frame]
            node2 = self.bot_data[bot_name][self.frame+1]

            print(self.vertices[node1])
            print(self.vertices[node2])
            #print(self.vertices)

            bot.position = (node1/10., node2/10., 0)

        self.frame += 1
