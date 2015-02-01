"""

"""

import os
import sys
import math
import pickle
import mathutils as mu
import networkx as nx
import logging

import gridbots

import bge

# Must match that of the BGE!! (fps)
BLENDER_FPS = 40

# Default 2x real time
DEFAULT_SPEED = 2.0

# TODO make this come from data
DEFAULT_RATE = 120


class BlenderDrawer():

    """
    Three-dimensional renderer class for gridbots simulations. Takes in a paths file and
    uses the Blender Game Engine to show a realistic 3D simulation.

    """

    def __init__(self, paths_name, speed=DEFAULT_SPEED):

        self.logger = logging.getLogger(__name__)

        # Read the paths file
        paths_file = os.path.join(gridbots.path, 'spec', 'paths', '{}.pickle'.format(paths_name))
        with open(paths_file, 'rb') as pf:
            paths_data = pickle.load(pf)

        # Get map data
        map_path = os.path.join(gridbots.path, 'spec', 'maps', '{}.gpickle'.format(paths_data["map_name"]))
        self.map = nx.read_gpickle(map_path)

        self.vertices = {}
        for n, d in self.map.nodes_iter(data=True):
            self.vertices[n] = mu.Vector((d['x'], d['y'], d['z']))

        self.edges = self.map.edges()

        # TODO read from data
        self.rate = DEFAULT_RATE

        self.speed = speed
        self.framerate = self.rate * self.speed
        self.superstep = self.framerate / BLENDER_FPS

        self.bot_data = paths_data["bots"]
        self.frames = paths_data["frames"]
        self.stations = paths_data["stations"]
        self.structure = paths_data["structure"]
        self.structure_pos = paths_data['structure_move_history']
        
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

        self.text = {
            'title': self.S.objects['text_title'],
            'status': self.S.objects['text_status'],
            'frame': self.S.objects['text_frame'],
            'time': self.S.objects['text_time'],
            'speed': self.S.objects['text_speed']
        }

        # Set framerate settings
        bge.logic.setMaxPhysicsFrame(1)
        bge.logic.setMaxLogicFrame(1)
        bge.logic.setLogicTicRate(BLENDER_FPS)
        bge.logic.setPhysicsTicRate(BLENDER_FPS)

        # Which simulation frame are we on?
        self.frame = 0.0
        self.time = 0.0
        self.frame_int = int(self.frame)

        self.bots = {}
        for bot in self.bot_data.keys():
            self.bots[bot] = self.S.addObject(self.bot_data[bot]['type'], self.C.owner)
            self.bots[bot].orientation = (0, 0, math.pi/2)

        self.b_stations = []
        for station_type in self.stations:

            for station in self.stations[station_type]:

                b_station = self.S.addObject(station_type, self.C.owner)
                self.b_stations.append(b_station)

                b_station.position = self.vertices[station.pos]
                b_station.position.z += 0.05

        self.b_structure = {}

        # Start in paused state to allow for loading the graphics
        self.paused = True
        self.logger.info('Hit [p] to start playback.')

        # Draw the scene
        self.render()

    def update(self):

        self.handle_keys()
        self.handle_camera()
        self.handle_text()

        self.framerate = self.rate * self.speed
        self.superstep = self.framerate / BLENDER_FPS

        if self.paused:
            return

        self.render()

        self.logger.debug('------- frame {} -------'.format(self.frame_int))

        self.frame += self.superstep
        self.time += self.superstep / self.rate

        if self.frame < 0:
            self.frame = 0
            self.time = 0

        elif self.frame > self.frames - 1:
            self.frame = self.frames - 1
            self.time -= self.superstep / self.rate

        self.frame_int = int(self.frame)

    def render(self):

        if self.frame > self.frames - 1:
            return

        for bot_name, bot in self.bots.items():

            node = self.bot_data[bot_name]['move_history'][self.frame_int]
            bot.position = self.vertices[node]

            z_rot = self.bot_data[bot_name]['rot_history'][self.frame_int]
            bot.orientation = (0, 0, z_rot)

        for frame, edge in self.structure:

            if frame <= self.frame_int:

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

    def handle_text(self):

        self.text['speed'].text = 'Speed: {:.2f}x'.format(self.speed)
        self.text['frame'].text = 'Frame: {}'.format(self.frame_int)
        self.text['time'].text = 'Time: {:.2f}s'.format(self.time)

        if self.paused:
            state_text = 'Paused '
        else:
            state_text = 'Playing'
        self.text['status'].text = 'Status: {}'.format(state_text)

    def handle_keys(self):

        for key, status in self.keyboard.events:

            if key == bge.events.XKEY:
                if status == bge.logic.KX_INPUT_JUST_ACTIVATED:
                    self.logger.info('X pressed, exiting.')
                    sys.exit(0)

            if key == bge.events.PKEY:
                if status == bge.logic.KX_INPUT_JUST_ACTIVATED:
                    if self.paused:
                        self.logger.info('Playing simulation.')
                        self.paused = False
                    else:
                        self.logger.info('Pausing simulation.')
                        self.paused = True

            if key == bge.events.IKEY:
                if status == bge.logic.KX_INPUT_JUST_ACTIVATED:
                    for bot in self.bots:
                        self.logger.info('Bot %s: Pos: %s, Rot: %s', bot,
                                         self.bot_data[bot]['move_history'][self.frame_int],
                                         self.bot_data[bot]['rot_history'][self.frame_int])

            if key == bge.events.RKEY:
                if status == bge.logic.KX_INPUT_JUST_ACTIVATED:
                    self.logger.info('Reversing speed.')
                    self.speed *= -1

            if key == bge.events.EQUALKEY:
                self.logger.info('Speeding up.')
                self.speed = self.speed * 1.01 + 0.01

            if key == bge.events.MINUSKEY:
                self.logger.info('Slowing down.')
                self.speed = self.speed * 0.99 - 0.01

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
