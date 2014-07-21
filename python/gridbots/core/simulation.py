"""

"""

import os
import yaml
import logging

import gridbots
from gridbots import utils
from gridbots.core.job import Structure


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

        sim_path = os.path.join(gridbots.path, 'simulations', '{}.yml'.format(sim_name))

        # Read the simulation file
        with open(sim_path) as sf:
            self.sim_data = yaml.load(sf.read())

        # Get names
        self.sim_name = sim_name
        self.structure_name = self.sim_data["structure"]
        self.map_name = self.sim_data["map"]

        # Parse the map file
        map_path = os.path.join(gridbots.path, 'maps', '{}.yml'.format(self.map_name))
        self.map = utils.graph.read_graph(map_path)

        # Parse the structure file
        structure_path = os.path.join(gridbots.path, 'structures',
                                      '{}.yml'.format(self.structure_name))
        structure_graph = utils.graph.read_graph(structure_path)
        self.structure = Structure(structure_graph)

        # Iterate through the waypoints and create Stations
        self.stations = utils.parse.parse_stations(self.sim_data['stations'])

        self.job_queue = utils.planning.create_job_queue(
            self.structure,
            self.sim_data['job_types']
        )

        self.job_queue = self.structure.jobs_todo

        # Iterate through the input file and create bots
        self.bots = utils.parse.parse_bots(
            self.sim_data['bots'],
            self
        )

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
            len(self.map.nodes())
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
        return '[Simulation] Bots: {}'.format(len(self.bots))

    def plan_tasks(self):

        # Task planning for jobs
        utils.planning.plan_paths(
            frame=self.frame,
            graph=self.map,
            bots=self.bots,
            stations=self.stations,
            structure=self.structure
        )

    def update(self):

        self.frame += 1
        self.time += self.TIME_PER_FRAME

        logging.info('----- frame: {} time: {} -----'.format(self.frame, self.time))

        self.plan_tasks()

        for bot in self.bots:

            # Move a step if it has one
            bot.update()

        for station_type in self.stations:
            for station in self.stations[station_type]:
                station.wait_time -= self.TIME_PER_FRAME
                if station.wait_time < 0:
                    station.wait_time = 0.0
                print('{}, wait time {}'.format(station, station.wait_time))

    def run(self):

        self.running = True

        while self.running:

            self.update()

            if all([j.finished for j in self.job_queue]):
                if all([b.at_home() for b in self.bots]):
                    logging.info('ALL JOBS COMPLETE!!')
                    self.status = self.STATUS["success"]
                    break

            #if self.frame == 1000:
            #    break

            if self.interactive:
                input('Enter to continue: ')
        # Add the last frame to the move history
        for bot in self.bots:
            bot.move_history.append(bot.pos)

        paths_name = self.output()
        return paths_name

    def output(self):

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

        output["bots"] = {}
        for bot in self.bots:
            output["bots"][bot.name] = {}
            output["bots"][bot.name]['type'] = bot.type
            output["bots"][bot.name]['move_history'] = bot.move_history
            output["bots"][bot.name]['move_history'].append(bot.move_history[-1])

        # Create the paths directory if needed
        paths_dir = "paths"
        if not os.path.exists(paths_dir):
            os.makedirs(paths_dir)

        # Create and write to the paths file
        paths_name = "paths_{}".format(self.sim_name)
        paths_path = os.path.join(gridbots.path, 'paths', '{}.yml'.format(paths_name))
        with open(paths_path, 'w') as t_file:
            t_file.write(yaml.dump(output))

        return paths_name
