"""

"""

import os
import yaml
import logging
import networkx as nx

import gridbots
from gridbots import utils
from gridbots.core.job import Structure
from gridbots.controllers.single_routine import SingleRoutineConroller


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

    # Physical time passed per frame (seconds)
    TIME_PER_FRAME = 0.1

    def __init__(self, sim_name, interactive=False):

        """
        Read in all simulation data from the given file and linked files. This includes
        the map graph, the target structure graph, bots, stations, and job types.

        """

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
        #map_path = os.path.join(gridbots.path, 'spec', 'maps', '{}.yml'.format(self.map_name))
        #self.map = utils.graph.read_graph(map_path)
        map_path = os.path.join(gridbots.path, 'spec', 'maps', '{}.gpickle'.format(self.map_name))
        self.map = nx.read_gpickle(map_path)

        # Parse the structure file
        structure_path = os.path.join(gridbots.path, 'spec', 'structures',
                                      '{}.yml'.format(self.structure_name))
        structure_graph = utils.graph.read_graph(structure_path)
        self.structure = Structure(structure_graph)

        # Iterate through the waypoints and create Stations
        self.stations = utils.parse.parse_stations(self.sim_data['stations'], self.node_aliases)

        # Parse routines from script files
        self.routine = utils.parse.parse_routine(self.sim_data['routine'])

        # self.job_queue = utils.planning.create_job_queue(
        #     self.structure,
        #     self.sim_data['job_types']
        # )

        self.job_queue = []  # self.structure.jobs_todo

        # Iterate through the input file and create bots
        self.bots = utils.parse.parse_bots(
            self.sim_data['bots'],
            self
        )

        self.controller = SingleRoutineConroller(self.bots, self.map, self.routine)
        self.control_inputs = {}

        logging.debug('Simulating {}'.format(
            self.sim_name
        ))

        logging.debug("----- STRUCTURE -----")
        logging.info('Build a truss with {} rods and {} nodes.'.format(
            len(self.structure.g.edges()),
            len(self.structure.g.nodes()),
            ))

        logging.debug("----- MAP -----")
        logging.info('Map {} has {} nodes.'.format(
            self.map_name,
            self.map.number_of_nodes()
        ))

        logging.debug("----- BOTS -----")
        for bot in self.bots:
            logging.debug(bot)

        logging.debug("----- STATIONS -----")
        for station_type in self.stations.keys():
            logging.debug('* {}'.format(station_type))
            for station in self.stations[station_type]:
                logging.debug('  {}'.format(station))

        logging.debug("------ JOBS -----")
        for job in self.job_queue:
            logging.debug(job)

        # Count frames
        self.frame = 0

        # Simulation time
        self.time = 0

        # Simulation status
        self.status = self.STATUS["in_progress"]

        self.running = False

        self.interactive = interactive

    def __str__(self):

        """
        String representation of the simulation object.

        """

        return '[Simulation] Bots: {}'.format(len(self.bots))

    # def plan_tasks(self):
    #
    #     # Task planning for jobs
    #     utils.planning.plan_paths(
    #         frame=self.frame,
    #         graph=self.map,
    #         bots=self.bots,
    #         stations=self.stations,
    #         structure=self.structure
    #     )

    def update(self):
        """
        Process one frame for all bots, including path planning and motion.

        """

        self.time += self.TIME_PER_FRAME

        # logging.debug('----- frame: %s time: %s -----', self.frame, self.time)

        # Run state machine for each bot
        for bot in self.bots:
            bot.update()

        # # Update structure location
        # try:
        #     structure_station = self.stations['attach_rod'][0]
        #     node_data = self.map.node[structure_station.pos]
        #     coords = node_data['x'], node_data['y'], node_data['z']
        # except KeyError:
        #     coords = [0, 0, 0]
        # self.structure.move_history.append(coords)
        #
        # # Print wait times for each station
        # for station_type in self.stations:
        #     for station in self.stations[station_type]:
        #         station.wait_time -= self.TIME_PER_FRAME
        #         if station.wait_time < 0:
        #             station.wait_time = 0.0
        #         # logging.debug('%s, wait time %s'.format(station, station.wait_time))

        self.frame += 1

    def run(self):

        """
        Main loop, update until all jobs are complete.

        """

        self.running = True

        while self.running:

            self.update()

            self.control_inputs = self.controller.step(self.frame)

            if self.controller.finished:
                break

            if self.interactive:
                input('Enter to continue: ')

        # Update structure location
        # TODO this is a copy of update function
        try:
            structure_station = self.stations['attach_rod'][0]
            node_data = self.map.node[structure_station.pos]
            coords = node_data['x'], node_data['y'], node_data['z']
        except KeyError:
            coords = [0, 0, 0]
        self.structure.move_history.append(coords)

        # Add the last frame to the move history
        for bot in self.bots:
            bot.move_history.append(bot.pos)

        paths_name = self.output()
        return paths_name

    def output(self):

        """
        Write the results of the simulation, along with the trajectories of all
        bots and resources, to a paths file.

        """

        logging.info('')
        logging.info('===============================')

        output = {}

        if self.status == self.STATUS["success"]:
            logging.info('Simulation finished successfully!')
        elif self.status == self.STATUS["traffic_jam"]:
            logging.error('Simulation stuck in a traffic jam!')
        elif self.status == self.STATUS["in_progress"]:
            logging.error('Output called but simulation still in progress!')

        output["status"] = [s for s, val in self.STATUS.items() if val == self.status][0]

        output["map_name"] = self.map_name
        output["sim_name"] = self.sim_name

        output["frames"] = len(self.bots[0].move_history)

        output["stations"] = self.stations
        output["structure"] = self.structure.completion_times

        output['structure_move_history'] = self.structure.move_history

        output["bots"] = {}
        for bot in self.bots:
            output["bots"][bot.name] = {}
            output["bots"][bot.name]['type'] = bot.type
            output["bots"][bot.name]['move_history'] = bot.move_history
            output["bots"][bot.name]['move_history'].append(bot.move_history[-1])
            output["bots"][bot.name]['rot_history'] = bot.rot_history
            output["bots"][bot.name]['rot_history'].append(bot.rot_history[-1])

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
            #t_file.write(yaml.dump(output))

        return paths_name
