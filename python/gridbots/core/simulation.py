"""

"""

import os
import yaml

from gridbots.core.bot import Bot

from gridbots.utils.graph import read_graph
from gridbots.utils.planning import plan_paths

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
        sim_file ='simulations/{}.yml'.format(sim_name)
        with open(sim_file) as sf:
            sim_data = yaml.load(sf.read())

        # Store names
        self.sim_name = sim_name
        self.structure_name = sim_data["structure"]
        self.map_name = sim_data["map"]

        # Store waypoints
        self.waypoints = sim_data["waypoints"]

        # Parse the map file
        self.map = read_graph("maps/{}.yml".format(self.map_name))

        # Parse the structure file
        self.structure = read_graph("structures/{}.yml".format(self.structure_name))

        print('----- Creating bots -----')
        # List of bots in the simulation
        self.bots = []

        # Iterate through the input file and create bots
        for bot_name, bot_data in sim_data['bots'].items():

            # Create a bot
            bot = Bot(
                    name=bot_name,
                    position=bot_data['position'],
                    orientation=bot_data['orientation'],
                    sim=self
                )

            # Add it to our list
            self.bots.append(bot)

            # Queue all goal positions
            #for vertex in bot_data['goals']:
            #    bot.add_goal(vertex)

        # Path planning to build structure
        plan_paths(self.bots, self.map, self.waypoints, self.structure)

        # Count frames
        self.frame = 0

        # Simulation status
        self.status = self.STATUS["in_progress"]

    def __str__(self):
        return '[Simulation] Bots: {}'.format(len(bots))

    def update(self):

        self.frame += 1
        print('----- frame: {} -----'.format(self.frame))

        status = [(bot.pos, bot.current_goal) for bot in self.bots]

        for bot in self.bots:

            # Move a step if it has one
            bot.update()

            # Output the bot's current status
            bot.print_status()

        new_status = [(bot.pos, bot.current_goal) for bot in self.bots]

        # Nothing has changed, but robots are not
        # all at their goals!
        if (status == new_status):

            for bot in self.bots:
                if not bot.at_goal():
                    self.status = self.STATUS["traffic_jam"]
                    self.running = False
                    return

            self.status = self.STATUS["success"]
            self.running = False
    
    def run(self):

        self.running = True

        while self.running:
            self.update()

        paths_name = self.output()
        return paths_name

    def output(self):

        print('')
        print('===============================')

        output = {}

        if self.status == self.STATUS["success"]:
            print('Simulation finished successfully!')
        elif self.status == self.STATUS["traffic_jam"]:
            print('ERROR: Simulation stuck in a traffic jam!')
        elif self.status == self.STATUS["in_progress"]:
            print('ERROR: Output called but simulation still in progress!')


        output["status"] =  (s for s,val in self.STATUS.items() if val==self.status).next()

        output["map_name"] = self.map_name
        output["sim_name"] = self.sim_name

        output["frames"] = len(self.bots[0].move_history) - 1

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
