"""

"""

import os
import sys
import yaml
from pprint import pprint, pformat
import logging
import networkx as nx
import pickle
import shutil

import gridbots
from gridbots import utils
from gridbots.core.bot import Bot
from gridbots.core.structure import Structure
from gridbots.controllers.single_routine import RoutineController
from gridbots.controllers.lattice_builder import LatticeController
from gridbots.utils.simstate import SimulationState

STATES_PER_FILE = 10000
FRAMES_PER_STATE = 6


class Simulation:

    """
    Top-level simulation class. Takes a simulation file as input and outputs a paths
    file specifying the trajectories of all bots and resources.

    """

    # Simulation states
    STATUS = {
        'in_progress': 0,
        'success': 1,
        'traffic_jam': 2
    }

    # Default framerate of the system
    DEFAULT_RATE = 120

    def __init__(self, sim_name):
        """
        Read in all simulation data from the given file and linked files. This includes
        the map graph, the target structure graph, bots, stations, and job types.

        """

        self.logger = logging.getLogger(__name__)

        sim_path = os.path.join(gridbots.path, 'spec', 'simulations', '{}.yml'.format(sim_name))

        # Read the simulation file
        with open(sim_path) as sf:
            self.sim_data = yaml.load(sf.read())

        # Get names
        self.sim_name = sim_name
        self.map_name = self.sim_data["map"]
        self.node_aliases = self.sim_data['node_aliases']

        # Parse the map file
        map_path = os.path.join(gridbots.path, 'spec', 'maps', '{}.gpickle'.format(self.map_name))
        self.map = nx.read_gpickle(map_path)

        # Iterate through the input file and create bots
        self.bots = utils.parse.parse_bots(
            self.sim_data['bots'],
            self.node_aliases,
            self.map
        )
        self.bot_dict = {b.name: b for b in self.bots}

        # Create a structure object
        self.structure = Structure(self)

        # Controller that provides control inputs for each time step
        controller_type = self.sim_data['controller']['type']
        if controller_type == 'LatticeController':
            controller_class = LatticeController
        elif controller_type == 'RoutineController':
            controller_class = RoutineController
        else:
            raise Exception('Unknown controller type: {}'.format(controller_type))

        self.controller = controller_class(self, self.sim_data['controller']['options'])

        # Count frames
        self.frame = 0

        # Simulation time
        self.time = 0

        # Simulation status
        self.status = self.STATUS["in_progress"]

        self.to_exit = False

        # Current system rate
        self.rate = self.DEFAULT_RATE

        # Create the paths directory if needed
        top_paths_dir = os.path.join(gridbots.path, 'spec', 'paths')
        if not os.path.exists(top_paths_dir):
            os.makedirs(top_paths_dir)

        # Create the simulation-specific directory in paths
        self.paths_dir = os.path.join(top_paths_dir, self.sim_name)

        if os.path.exists(self.paths_dir):
            shutil.rmtree(self.paths_dir)
        os.makedirs(self.paths_dir)

        # First frame that we are currently holding states for in memory
        self.new_file_frame = self.frame

        # List of frame: SimulationStates since self.new_file_frame
        self.states = {}

        self.full_state = None

        #self.record_state({})

        self.last_control_input = {}

    def __str__(self):

        """
        String representation of the simulation object.

        """

        return '[{}] Bots: {}'.format(self.sim_name, len(self.bots))

    def update(self):
        """
        Process one frame for all bots, including path planning and motion.

        """

        if self.frame % 1000 == 0:
            self.logger.info('----- frame: {} time: {:.2f} -----'.format(self.frame, self.time))

        # If complete, exit
        if self.controller.finished:
            self.status = self.STATUS['success']
            self.to_exit = True
            return

        # Run the controller to get inputs for this time step
        control_inputs = self.controller.step(self.frame)
        self.last_control_input = control_inputs

        if not control_inputs:
            return

        # Update each bot based on the inputs
        for bot in self.bots:
            bot.update(control_inputs)

        self.structure.update(control_inputs)

        self.record_state(control_inputs)

        # Update the simulation metadata
        self.time += 1 / self.rate
        self.frame += 1

    def record_state(self, control_inputs):

        if self.frame % FRAMES_PER_STATE == 0:

            s = SimulationState(self.frame)

            s.set_bots(self.bot_dict, self.full_state)
            s.set_structure(self.structure, self.full_state)

            if 'script' in control_inputs:
                s.set_scripts(control_inputs['script'], self.time, self.full_state)

            self.states[self.frame] = s.serialize()

            # Update full_state with everything
            if not self.full_state:
                self.full_state = SimulationState(self.frame)
            else:
                self.full_state.frame = self.frame
            self.full_state.set_bots(self.bot_dict)
            self.full_state.set_structure(self.structure)
            if 'script' in control_inputs:
                self.full_state.set_scripts(control_inputs['script'], self.time)

        if len(self.states) >= STATES_PER_FILE:
            self.dump_data()

    def run(self):
        """
        Main loop, update until all jobs are complete.

        """

        while not self.to_exit:
            self.update()

        # Dump the rest of the states
        self.dump_data()

        # Dump the simulation metadata
        self.dump_meta()

        return self.sim_name

    def print_status(self):

        self.logger.info(self)
        self.logger.info('Frame: %s, Time: %s', self.frame, self.time)

        for bot in self.bots:
            self.logger.info(bot)

    def dump_data(self):

        paths_file = os.path.join(self.paths_dir, '{}.pickle'.format(self.new_file_frame))
        with open(paths_file, 'wb') as f:
            pickle.dump(self.states, f)

        self.new_file_frame = self.frame + FRAMES_PER_STATE
        self.states = {}

    def dump_meta(self):

        meta_file = os.path.join(self.paths_dir, 'meta.yml')
        with open(meta_file, 'w') as f:
            f.write(yaml.dump({
                'sim_name': self.sim_name,
                'num_frames': self.frame,
                'num_rods': len(self.structure.rods),
                'num_bots': len(self.bots),
                'end_time': self.time,
                'bots': {b.name: b.type for b in self.bots},
                'rods': {rod_id: rod['type'] for rod_id, rod in self.structure.rods.items()}
                }))
