"""

"""

import sys
import math
import yaml
import mathutils as mu

from gridbots.utils.graph import read_graph_data

import bge

# Must match that of the BGE!! (fps)
BLENDER_FPS = 40

# Desired framerate of simulation (fps)
FRAMERATE = 10


class BlenderDrawer():

    def __init__(self, paths_name, framerate=FRAMERATE):

        # Read the paths file
        paths_file ='paths/{}.yml'.format(paths_name)
        with open(paths_file) as pf:
            paths_data = yaml.load(pf.read())

        # Get map data
        self.vertices, self.edges = read_graph_data("maps/{}.yml".format(paths_data["map_name"]))

        # Convert vertex data to 3D mathutils.Vectors
        for v_name, v in self.vertices.items():
            self.vertices[v_name] = mu.Vector(v).to_3d()

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
            self.nodes[name].position = coords

        self.b_edges = []
        for e in self.edges:

            b_edge = self.S.addObject('Edge', self.C.owner)
            self.b_edges.append(b_edge)

            v1 = self.vertices[e[0]]
            v2 = self.vertices[e[1]]

            midpoint = v1.lerp(v2, 0.5)
            b_edge.position = midpoint

            # Set rotation
            unit = mu.Vector((1, 0, 0))
            quat = unit.rotation_difference(v2-v1)
            b_edge.applyRotation(quat.to_euler('XYZ'))

        self.b_stations = []
        for station_type in self.stations:

            for station in self.stations[station_type]:

                b_station = self.S.addObject(station_type, self.C.owner)
                self.b_stations.append(b_station)

                b_station.position = self.vertices[station.pos]

        self.b_structure = {}

    def update(self):

        if self.frame > self.frames - 1:
            return

        for bot_name, bot in self.bots.items():
            
            node1 = self.bot_data[bot_name]['move_history'][self.frame]
            node2 = self.bot_data[bot_name]['move_history'][self.frame+1]

            c1 = self.vertices[node1]
            c2 = self.vertices[node2]

            fraction = self.substep / float(self.substeps)

            pos = c1.lerp(c2, fraction)
            bot.position = pos

        for frame, edge in self.structure:

            if frame <= self.frame:

                if edge not in self.b_structure.keys():

                    self.b_structure[edge] = self.S.addObject('Edge', self.C.owner)

                    v1 = mu.Vector(edge[0])
                    v2 = mu.Vector(edge[1])
                    midpoint = v1.lerp(v2, 0.5)
                    self.b_structure[edge].position = midpoint + mu.Vector((0, 0, 2))

                    unit = mu.Vector((1, 0, 0))
                    quat = unit.rotation_difference(v2-v1)

                    self.b_structure[edge].applyRotation(quat.to_euler('XYZ'))

        self.substep += 1

        if self.substep == self.substeps:
            print('------- frame {} -------'.format(self.frame))
            self.substep = 0
            self.frame += 1

# --------------------------------------------------

renderer = None


def start_rendering():

    global renderer

    if len(sys.argv) >= 9:
        paths_name = sys.argv[8]
    else:
        paths_name = 'paths_two_cross'

    renderer = BlenderDrawer(paths_name=paths_name)


def render_frame():

    renderer.update()
