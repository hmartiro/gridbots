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
from gridbots.controllers.single_routine import SingleRoutineConroller
from gridbots.utils.simstate import SimulationState

STATES_PER_FILE = 10000


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
        self.structure_name = self.sim_data["structure"]
        self.map_name = self.sim_data["map"]
        self.node_aliases = self.sim_data['node_aliases']

        # Parse the map file
        map_path = os.path.join(gridbots.path, 'spec', 'maps', '{}.gpickle'.format(self.map_name))
        self.map = nx.read_gpickle(map_path)

        # Iterate through the waypoints and create Stations
        self.stations = utils.parse.parse_stations(self.sim_data['stations'], self.node_aliases)

        # Parse routines from script files
        self.routine = utils.parse.parse_routine(self.sim_data['routine'])

        # Iterate through the input file and create bots
        self.bots = utils.parse.parse_bots(
            self.sim_data['bots'],
            self.node_aliases,
            self.map
        )
        self.bot_dict = {b.name: b for b in self.bots}

        # Parse the structure file
        structure_path = os.path.join(gridbots.path, 'spec', 'structures',
                                      '{}.yml'.format(self.structure_name))
        structure_graph = utils.graph.read_graph(structure_path)
        self.structure = Structure(self, structure_graph)

        # Controller that provides control inputs for each time step
        self.controller = SingleRoutineConroller(self.bots, self.map, self.routine)

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
        shutil.rmtree(self.paths_dir)
        if not os.path.exists(self.paths_dir):
            os.makedirs(self.paths_dir)

        # First frame that we are currently holding states for in memory
        self.new_file_frame = self.frame

        # List of frame: SimulationStates since self.new_file_frame
        self.states = {}

        self.record_state({})

        # ---------------------
        # Debug info
        # ---------------------

        self.logger.debug('Simulating {}'.format(
            self.sim_name
        ))

        self.logger.debug("----- STRUCTURE -----")
        self.logger.info('Build a truss with {} rods and {} nodes.'.format(
            len(self.structure.g.edges()),
            len(self.structure.g.nodes()),
            ))

        self.logger.debug("----- MAP -----")
        self.logger.info('Map {} has {} nodes.'.format(
            self.map_name,
            self.map.number_of_nodes()
        ))

        self.logger.debug("----- BOTS -----")
        for bot in self.bots:
            self.logger.debug(bot)

        self.logger.debug("----- STATIONS -----")
        for station_type in self.stations.keys():
            self.logger.debug('* {}'.format(station_type))
            for station in self.stations[station_type]:
                self.logger.debug('  {}'.format(station))

    def __str__(self):

        """
        String representation of the simulation object.

        """

        return '[Simulation] Bots: {}'.format(len(self.bots))

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

        s = SimulationState(self.frame)

        s.set_bots(self.bots)
        s.set_structure(self.structure)

        if 'script' in control_inputs:
            s.set_scripts(control_inputs['script'])

        self.states[self.frame] = s.serialize()

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

        self.new_file_frame = self.frame + 1
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
