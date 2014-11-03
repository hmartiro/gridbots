"""

"""

import os
import sys
import math
import yaml
import mathutils as mu
import networkx as nx

import gridbots
from gridbots.utils.graph import read_graph_data

import bge

# Must match that of the BGE!! (fps)
BLENDER_FPS = 40

# Desired framerate of simulation (fps)
FRAMERATE = 10


class BlenderDrawer():

    """
    Three-dimensional renderer class for gridbots simulations. Takes in a paths file and
    uses the Blender Game Engine to show a realistic 3D simulation.

    """

    def __init__(self, paths_name, framerate=FRAMERATE):

        # Read the paths file
        paths_file = os.path.join(gridbots.path, 'spec', 'paths', '{}.yml'.format(paths_name))
        with open(paths_file) as pf:
            paths_data = yaml.load(pf.read())

        # Get map data
        #map_file = os.path.join(gridbots.path, 'spec', 'maps', '{}.yml'.format(paths_data["map_name"]))
        #self.vertices, self.edges = read_graph_data(map_file)
        map_path = os.path.join(gridbots.path, 'spec', 'maps', '{}.gpickle'.format(paths_data["map_name"]))
        self.map = nx.read_gpickle(map_path)

        self.vertices = {}
        for n, d in self.map.nodes_iter(data=True):
            self.vertices[n] = mu.Vector((d['x'], d['y'], d['z']))

        self.edges = self.map.edges()

        # Convert vertex data to 3D mathutils.Vectors
        #for v_name, v in self.vertices.items():
        #    self.vertices[v_name] = mu.Vector(v).to_3d()

        self.framerate = framerate
        self.substeps = int(float(BLENDER_FPS) / float(self.framerate))

        self.bot_data = paths_data["bots"]

        self.frames = paths_data["frames"]

        self.stations = paths_data["stations"]

        self.structure = paths_data["structure"]

        self.structure_pos = paths_data['structure_move_history']

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

        # Camera object
        self.camera = self.S.objects['Camera']

        # Mouse information
        self.mouse = self.S.objects['Navigator'].controllers['Mouse'].sensors['Mouse']
        self.keyboard = self.S.objects['Navigator'].controllers['Keyboard'].sensors['Keyboard']
        self.mouse_x = 0.0
        self.mouse_y = 0.0
        self.mouse_left = False
        self.mouse_right = False

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
        # self.nodes = {}
        # for name, coords in self.vertices.items():
        #     self.nodes[name] = self.S.addObject('Node', self.C.owner)
        #     self.nodes[name].position = coords
        #
        # self.b_edges = []
        # for e in self.edges:
        #
        #     b_edge = self.S.addObject('Edge', self.C.owner)
        #     self.b_edges.append(b_edge)
        #
        #     v1 = self.vertices[e[0]]
        #     v2 = self.vertices[e[1]]
        #
        #     midpoint = v1.lerp(v2, 0.5)
        #     b_edge.position = midpoint
        #
        #     # Set rotation
        #     unit = mu.Vector((1, 0, 0))
        #     quat = unit.rotation_difference(v2-v1)
        #     b_edge.applyRotation(quat.to_euler('XYZ'))
        #
        #     # Set scale
        #     dist = (v2-v1).magnitude
        #     b_edge.localScale = [dist, 1, 1]

        self.b_stations = []
        for station_type in self.stations:

            for station in self.stations[station_type]:

                b_station = self.S.addObject(station_type, self.C.owner)
                self.b_stations.append(b_station)

                b_station.position = self.vertices[station.pos]
                b_station.position.z += 0.05

        self.b_structure = {}

    def update(self):

        self.handle_camera()

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

                    self.b_structure[edge] = self.S.addObject('edge_structure', self.C.owner)

                    v1 = mu.Vector(edge[0])
                    v2 = mu.Vector(edge[1])
                    midpoint = v1.lerp(v2, 0.5)
                    self.b_structure[edge].position = midpoint

                    # TODO interpolate frames like for bots
                    base_pos = mu.Vector(self.structure_pos[self.frame])
                    self.b_structure[edge].position = self.b_structure[edge].position + base_pos

                    unit = mu.Vector((1, 0, 0))
                    quat = unit.rotation_difference(v2-v1)

                    self.b_structure[edge].applyRotation(quat.to_euler('XYZ'))

                    # Set scale
                    dist = (v2-v1).magnitude
                    self.b_structure[edge].localScale = [dist, 1, 1]

        self.substep += 1

        if self.substep == self.substeps:
            print('------- frame {} -------'.format(self.frame))
            self.substep = 0
            self.frame += 1

    def handle_camera(self):

        # Get current window dimensions (pixel)
        width = bge.render.getWindowWidth()
        height = bge.render.getWindowHeight()

        # Scale mouse position to [0, 1] in x and y
        x = self.mouse.position[0] / width
        y = 1 - self.mouse.position[1] / height

        # Mouse button presses
        left_pressed = self.mouse.getButtonStatus(bge.events.LEFTMOUSE) > 0
        right_pressed = self.mouse.getButtonStatus(bge.events.RIGHTMOUSE) > 0

        left_ctrl = self.keyboard.getKeyStatus(bge.events.LEFTCTRLKEY) > 0
        left_shift = self.keyboard.getKeyStatus(bge.events.LEFTSHIFTKEY) > 0

        # Get movement
        dx = x - self.mouse_x
        dy = y - self.mouse_y

        zoom_scale = 20
        pan_scale = 10
        look_scale = 1

        if left_ctrl and left_pressed:
            m = mu.Vector((0, 0, -dy)) * zoom_scale
            self.camera.applyMovement(m, True)

        elif left_shift and left_pressed:
            m = mu.Vector((-dx, -dy, 0)) * pan_scale
            self.camera.applyMovement(m)

        elif left_pressed:
            m = mu.Vector((-dy, dx, 0)) * look_scale
            self.camera.applyRotation(m, True)

        self.mouse_x = x
        self.mouse_y = y
        self.mouse_left = left_pressed
        self.mouse_right = right_pressed

# --------------------------------------------------


# Must use a global variable here because of the way Blender
# makes calls to these functions.
renderer = None


def start_rendering():

    """
    Called by Blender once to create and initialize the renderer.

    """

    global renderer

    if len(sys.argv) >= 9:
        paths_name = sys.argv[8]
    else:
        paths_name = 'paths_two_cross'

    renderer = BlenderDrawer(paths_name=paths_name)


def render_frame():

    """
    Called each frame of the Blender Game Engine. This call updates all
    objects before Blender renders the frame.

    """

    renderer.update()
