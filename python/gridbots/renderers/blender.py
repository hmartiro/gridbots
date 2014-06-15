"""

"""

import math
import yaml
import mathutils

from gridbots.utils.graph import read_graph_data

import bge

# Must match that of the BGE!! (fps)
BLENDER_FPS = 40

# Desired framerate of simulation (fps)
FRAMERATE = 10

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

        self.stations = paths_data["stations"]

        self.structure = paths_data["structure"]

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

        # Set framerate settings
        bge.logic.setMaxPhysicsFrame(1)
        bge.logic.setMaxLogicFrame(1)
        bge.logic.setLogicTicRate(BLENDER_FPS)
        bge.logic.setPhysicsTicRate(BLENDER_FPS)

        # Which simulation frame are we on?
        self.frame = 0

        # Which substep of the simulation frame?
        self.substep = 0

        self.bots = {}
        for bot in self.bot_data.keys():
            self.bots[bot] = self.S.addObject(self.bot_data[bot]['type'], self.C.owner)
            self.bots[bot].orientation = (0, 0, math.pi/2)
            #print(dir(self.bots[bot]))

        # Draw nodes
        self.nodes = {}
        for name, coords in self.vertices.items():
            self.nodes[name] = self.S.addObject('Node', self.C.owner)
            self.nodes[name].position = (coords[0], coords[1], 0.)

        self.b_edges = []
        for e in self.edges:

            b_edge = self.S.addObject('Edge', self.C.owner)
            self.b_edges.append(b_edge)

            v1 = self.vertices[e[0]]
            v2 = self.vertices[e[1]]

            midpoint = interpolate(v1, v2, 0.5)
            b_edge.position = (midpoint[0], midpoint[1], 0)

            # Set rotation
            rad = get_angle(v1, v2)
            b_edge.applyRotation((0., 0., rad))

        self.b_stations = []
        for station_type in self.stations:

            for station in self.stations[station_type]:

                b_station = self.S.addObject(station_type, self.C.owner)
                self.b_stations.append(b_station)

                c = self.vertices[station.pos]
                b_station.position = (c[0], c[1], 0)

        self.b_structure = {}

    def update(self):

        if self.frame > self.frames - 1:
            return

        print('------- frame {} -------'.format(self.frame))

        for bot_name, bot in self.bots.items():
            
            node1 = self.bot_data[bot_name]['move_history'][self.frame]
            node2 = self.bot_data[bot_name]['move_history'][self.frame+1]

            c1 = self.vertices[node1]
            c2 = self.vertices[node2]

            fraction = self.substep / float(self.substeps)

            x = c1[0] * (1-fraction) + c2[0] * fraction
            y = c1[1] * (1-fraction) + c2[1] * fraction

            bot.position = (x, y, 0.)

        for frame, edge in self.structure:

            if frame <= self.frame:

                if edge not in self.b_structure.keys():
                    self.b_structure[edge] = self.S.addObject('Edge', self.C.owner)

                    midpoint = tuple(interpolate(edge[0], edge[1], 0.5))
                    self.b_structure[edge].position = midpoint
                    print((edge[0], edge[1]))
                    rad = get_angle(edge[0], edge[1])
                    self.b_structure[edge].applyRotation((0, 0, rad))
                    print(midpoint)
                    print(rad)
        self.substep += 1

        if self.substep == self.substeps:
            self.substep = 0
            self.frame += 1


def interpolate(start, end, fraction):
    """
    Interpolate between two vectors
    """
    return [n + fraction * (p-n) for n, p in zip(start, end)]


def get_angle(p, q):
    """
    Return the rotation angle between two 3D vectors, in radians.
    """
    dX = q[0] - p[0]
    dY = q[1] - p[1]
    dZ = q[2] - p[2]

    radX
    radZ = math.acos((dX)/math.sqrt((dX)**2 + (dY)**2))
    return rad


def get_angle_2D(p, q):
    """
    Return the direction, in radians, of the vector specified by the points p, q.
    """
    dX = q[0] - p[0]
    dY = q[1] - p[1]
    rad = math.acos((dX)/math.sqrt((dX)**2 + (dY)**2))
    return rad