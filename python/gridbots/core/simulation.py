"""

"""

import os
import yaml
import logging

from gridbots.core.bot import Bot
from gridbots.core.job import Job
from gridbots.core.job import Station

from gridbots import utils


class Simulation:
    """ The overall simulation class. """

    # Simulation states
    STATUS = {
        'in_progress': 0,
        'success': 1,
        'traffic_jam': 2
    }

    def __init__(self, sim_name):

        # Read the simulation file
        sim_file = 'simulations/{}.yml'.format(sim_name)
        with open(sim_file) as sf:
            self.sim_data = yaml.load(sf.read())

        # Get names
        self.sim_name = sim_name
        self.structure_name = self.sim_data["structure"]
        self.map_name = self.sim_data["map"]

        # Parse the map file
        self.map = utils.graph.read_graph("maps/{}.yml".format(self.map_name))

        # Parse the structure file
        self.structure = utils.graph.read_graph("structures/{}.yml".format(self.structure_name))

        # Iterate through the waypoints and create Stations
        self.stations = utils.parse.parse_stations(self.sim_data['stations'])

        # Create jobs from list (temporary)
        self.job_queue = utils.parse.parse_jobs(self.sim_data['jobs'])

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
            len(self.structure.es),
            len(self.structure.vs),
            ))

        logging.debug("----- MAP -----")
        logging.info('Map {} has {} nodes'.format(
            self.map_name,
            len(self.map.vs)
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

        # Simulation status
        self.status = self.STATUS["in_progress"]

        self.running = False

    def __str__(self):
        return '[Simulation] Bots: {}'.format(len(self.bots))

    def plan_tasks(self):

        # Task planning for jobs
        utils.planning.plan_paths(
            graph=self.map,
            bots=self.bots,
            stations=self.stations,
            jobs=self.job_queue
        )

    def update(self):

        self.frame += 1
        logging.info('----- frame: {} -----'.format(self.frame))

        self.plan_tasks()

        for bot in self.bots:

            # Move a step if it has one
            bot.update()

            if bot.at_goal():
                bot.last_at_goal = self.frame
            print('Last at goal: {}'.format(bot.last_at_goal))

    def run(self):

        self.running = True

        while self.running:

            self.update()

            if all([j.finished for j in self.job_queue]):
                if all([b.at_home() for b in self.bots]):
                    logging.info('ALL JOBS COMPLETE!!')
                    self.status = self.STATUS["success"]
                    break

            if self.frame == 1000:
                break

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

        output["status"] = (s for s, val in self.STATUS.items() if val == self.status).next()

        output["map_name"] = self.map_name
        output["sim_name"] = self.sim_name

        output["frames"] = len(self.bots[0].move_history) - 1

        output["stations"] = self.stations

        output["bots"] = {}
        for bot in self.bots:
            output["bots"][bot.name] = bot.move_history

        # Create the paths directory if needed
        paths_dir = "paths"
        if not os.path.exists(paths_dir):
            os.makedirs(paths_dir)

        # Create and write to the paths file
        paths_name = "paths_{}".format(self.sim_name)
        with open("paths/{}.yml".format(paths_name), 'w') as t_file:
            t_file.write(yaml.dump(output))

        return paths_name
