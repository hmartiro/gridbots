"""

"""

import os
import sys
import math
import yaml
import pickle
import mathutils as mu
import logging

import gridbots
from gridbots.utils.simstate import SimulationState
from gridbots.core.simulation import STATES_PER_FILE

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

    def get_state(self, frame):

        if frame not in self.states:

            base_frame = frame - frame % STATES_PER_FILE
            paths_file = os.path.join(
                gridbots.path, 'spec', 'paths', self.sim_name,
                '{}.pickle'.format(base_frame)
            )

            if not os.path.isfile(paths_file):
                return None

            with open(paths_file, 'rb') as f:
                self.states = pickle.load(f)

        return SimulationState.deserialize(self.states[frame])

    def __init__(self, sim_name, speed=DEFAULT_SPEED):

        self.logger = logging.getLogger(__name__)

        meta_path = os.path.join(gridbots.path, 'spec', 'paths', sim_name, 'meta.yml')
        with open(meta_path) as f:
            data = yaml.load(f.read())
            self.sim_name = data['sim_name']
            self.num_frames = data['num_frames']
            self.num_bots = data['num_bots']
            self.num_rods = data['num_rods']
            self.bot_data = data['bots']
            self.rod_data = data['rods']
            self.end_time = data['end_time']

        # TODO read from data
        self.rate = DEFAULT_RATE

        self.speed = speed
        self.framerate = self.rate * self.speed
        self.superstep = self.framerate / BLENDER_FPS

        self.states = {}

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
            'speed': self.S.objects['text_speed'],
            'scripts': self.S.objects['text_scripts']
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

        self.bot_objs = {}
        for bot_name, bot_type in self.bot_data.items():
            self.bot_objs[bot_name] = self.S.addObject(bot_type, self.C.owner)
            self.bot_objs[bot_name].orientation = (0, 0, math.pi/2)
            self.bot_objs[bot_name]['type'] = bot_type

        self.rod_objs = {}
        self.rod_type_to_model_map = {
            'h': 'rod_y',
            'v': 'rod_z'  # TODO this is awkward
        }
        self.bot_to_rod_pos_offset = {
            'bot_rod_h': mu.Vector([.47136, 0, .17335]),
            'bot_rod_v': mu.Vector([.47136, 0, .30]),
        }

        for rod_id, rod_type in self.rod_data.items():
            rod_type = self.rod_type_to_model_map[rod_type]
            self.rod_objs[rod_id] = self.S.addObject(rod_type, self.C.owner)
            self.rod_objs[rod_id].position = mu.Vector([0, 0, 100])

        self.stage_obj = self.S.objects['stage']

        self.structure = {}

        self.state = self.get_state(self.frame_int)
        if self.state is None:
            raise Exception('Could not find data for frame 0!')

        self.logger.info('Hit space to start playback.')

        self.paused = False

        # Draw the initial scene
        self.update()

        # Start in paused state to allow for loading the graphics
        self.paused = True

    def update(self):

        self.handle_keys(self.state)
        self.handle_camera(self.state)
        self.handle_text(self.state)

        self.framerate = self.rate * self.speed
        self.superstep = self.framerate / BLENDER_FPS

        if self.paused:
            return

        self.render(self.state)

        self.logger.debug('------- frame {} -------'.format(self.frame_int))

        self.frame += self.superstep
        self.time += self.superstep / self.rate

        if self.frame < 0:
            self.frame = 0
            self.time = 0
            self.paused = True

        elif self.frame > self.num_frames - 1:
            self.frame = self.num_frames - 1
            self.time = self.end_time
            self.paused = True

        self.frame_int = int(self.frame)
        self.state = self.get_state(self.frame_int)
        assert self.state is not None

    def render(self, state):

        if self.frame > self.num_frames - 1:
            return

        for bot_name, bot_state in state.bots.items():
            self.bot_objs[bot_name].position = bot_state[0]
            self.bot_objs[bot_name].orientation = mu.Euler([0, 0, bot_state[1]])

        # Move the stage
        stage_pos = mu.Vector(state.structure)
        self.stage_obj.position = stage_pos

        for rod_id, rod_data in state.rods.items():
            rod_type, rod_bot, rod_pos, rod_rot, rot_done = rod_data
            rod_obj = self.rod_objs[rod_id]

            # Rod is on a bot currently, draw it relative to bot's loc
            if rod_bot:
                bot_type = self.bot_objs[rod_bot]['type']
                bot_pos = self.bot_objs[rod_bot].position
                bot_ori = self.bot_objs[rod_bot].orientation

                bot_to_rod = self.bot_to_rod_pos_offset[bot_type]
                bot_to_rod_rotated = bot_ori * bot_to_rod

                rod_obj.position = bot_pos + bot_to_rod_rotated

                if bot_type == 'bot_rod_h':
                    rod_obj.orientation = bot_ori
                elif bot_type == 'bot_rod_v':
                    rod_obj.orientation = mu.Euler([math.pi/2, 0, 0])
                    rod_obj.orientation.rotate(bot_ori)
                else:
                    raise Exception('Unexpected bot type: {}'.format(bot_type))

                print('position of rod {}: {}'.format(rod_id, rod_obj.position))

            # Rod is on its own, just draw
            else:
                rod_obj.position = mu.Vector(rod_pos)
                rod_obj.orientation = mu.Vector(rod_rot)
                if rot_done:
                    rod_obj.position += mu.Vector(self.stage_obj.position)

                print('position of rod {}: {}'.format(rod_id, rod_obj.position))

    def handle_text(self, state):

        self.text['speed'].text = 'Speed: {:.2f}x'.format(self.speed)
        self.text['frame'].text = 'Frame: {}'.format(self.frame_int)
        self.text['time'].text = 'Time: {:.2f}s'.format(self.time)

        if self.paused:
            state_text = 'Paused '
        else:
            state_text = 'Playing'
        self.text['status'].text = 'Status: {}'.format(state_text)

        self.text['scripts'].text = ''
        for script in state.scripts:
            if script == 'simscript' or not script:
                continue
            self.text['scripts'].text += '\n' + str(script)

    def handle_keys(self, state):

        for key, status in self.keyboard.events:

            if key == bge.events.XKEY:
                if status == bge.logic.KX_INPUT_JUST_ACTIVATED:
                    self.logger.info('X pressed, exiting.')
                    sys.exit(0)

            if key == bge.events.SPACEKEY:
                if status == bge.logic.KX_INPUT_JUST_ACTIVATED:
                    if self.paused:
                        self.logger.info('Playing simulation.')
                        self.paused = False
                    else:
                        self.logger.info('Pausing simulation.')
                        self.paused = True

            if key == bge.events.IKEY:
                if status == bge.logic.KX_INPUT_JUST_ACTIVATED:
                    for bot in self.bot_objs:
                        self.logger.info('Bot %s: Pos: %s, Rot: %s', bot,
                                         bot.position,
                                         bot.orientation)

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

            if key == bge.events.RIGHTBRACKETKEY:
                if status == bge.logic.KX_INPUT_JUST_ACTIVATED:
                    self.logger.info('Doubling speed.')
                    self.speed *= 2.0

            if key == bge.events.LEFTBRACKETKEY:
                if status == bge.logic.KX_INPUT_JUST_ACTIVATED:
                    self.logger.info('Halving speed.')
                    self.speed *= 0.5

    def handle_camera(self, state):

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

    sim_name = sys.argv[8]
    renderer = BlenderDrawer(sim_name)


def render_frame():

    """
    Called each frame of the Blender Game Engine. This call updates all
    objects before Blender renders the frame.

    """

    renderer.update()
