"""

"""

import os
import sys
import yaml
from pprint import pprint, pformat
import logging
import networkx as nx

import gridbots
from gridbots import utils
from gridbots.core.bot import Bot
from gridbots.core.structure import Structure
from gridbots.controllers.single_routine import SingleRoutineConroller
from gridbots.utils.maputils import pos_from_node

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
        #pprint(self.routine)
        #sys.exit(1)
        # Iterate through the input file and create bots
        self.bots = utils.parse.parse_bots(
            self.sim_data['bots'],
            self
        )

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

        # History of scripts being run
        self.script_history = [[]]

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

        self.script_history.append(control_inputs['script'])

        # Update the simulation metadata
        self.time += 1 / self.rate
        self.frame += 1

    def run(self):
        """
        Main loop, update until all jobs are complete.

        """

        while not self.to_exit:
            self.update()

        return self.output()

    def print_status(self):

        self.logger.info(self)
        self.logger.info('Frame: %s, Time: %s', self.frame, self.time)

        for bot in self.bots:
            self.logger.info(bot)

    def output(self):
        """
        Write the results of the simulation, along with the trajectories of all
        bots and resources, to a paths file.

        """

        self.logger.info('')
        self.logger.info('===============================')

        output = {}

        if self.status == self.STATUS["success"]:
            self.logger.info('Simulation finished successfully!')
        elif self.status == self.STATUS["traffic_jam"]:
            self.logger.error('Simulation stuck in a traffic jam!')
        elif self.status == self.STATUS["in_progress"]:
            self.logger.error('Output called but simulation still in progress!')

        output["status"] = [s for s, val in self.STATUS.items() if val == self.status][0]

        output["map_name"] = self.map_name
        output["sim_name"] = self.sim_name

        output["frames"] = len(self.bots[0].move_history)

        output["stations"] = self.stations

        output["bots"] = {}
        for bot in self.bots:
            output["bots"][bot.name] = {}
            output["bots"][bot.name]['type'] = bot.type
            output["bots"][bot.name]['move_history'] = bot.move_history
            output["bots"][bot.name]['rot_history'] = bot.rot_history

        output["structure"] = {}
        output['structure']['move_history'] = self.structure.move_history

        output['script_history'] = self.script_history

        output['rod_history'] = self.structure.rod_history

        # Create the paths directory if needed
        paths_dir = os.path.join(gridbots.path, 'spec', 'paths')
        if not os.path.exists(paths_dir):
            os.makedirs(paths_dir)

        # Create and write to the paths file
        paths_name = "paths_{}".format(self.sim_name)
        paths_path = os.path.join(paths_dir, '{}.pickle'.format(paths_name))

        import pickle

        with open(paths_path, 'wb') as t_file:
            pickle.dump(output, t_file)

        return paths_name
