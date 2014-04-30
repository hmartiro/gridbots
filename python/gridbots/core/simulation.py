"""

"""

import yaml

from igraph import Graph, summary, plot

from gridbots.core.bot import Bot

class Simulation:
    """ The overall simulation class. """

    def __init__(self, simulation_file, renderer):

        print('Welcome to gridbots!')

        # Read the simulation file
        with open(simulation_file) as sim_file:
            sim_data = yaml.load(sim_file.read())
        map_filename = "maps/{}.yml".format(sim_data["map"])

        # Read the map file
        with open(map_filename) as map_file:
            map_data = yaml.load(map_file.read())

        # Extract data from the yaml
        vertices = map_data['vertices']
        edges = map_data['edges']

        # Find the outer dimensions of the map
        min_x = min_y = float("+inf")
        max_x = max_y = float("-inf")
        for v_id, v in vertices:
            if v[0] > max_x:
                max_x = v[0]
            if v[0] < min_x:
                min_x = v[0]
            if v[1] > max_y:
                max_y = v[1]
            if v[1] < min_y:
                min_y = v[1]
        self.map_dimensions = (min_x, max_x, min_y, max_y)

        self.graph = Graph()

        v_names = [v[0] for v in vertices]
        v_coords = [v[1] for v in vertices]

        self.graph.add_vertices(v_names)

        for v, v_coord in zip(self.graph.vs, v_coords):
            v["coords"] = v_coord

        #print([v for v in self.graph.vs])

        self.graph.add_edges(edges)

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

            # Queue all goal positions
            for vertex in bot_data['goals']:
                bot.add_goal(vertex)

            # Add it to our list
            self.bots.append(bot)

        # Count frames
        self.frame = 0

        # Create a renderer instance from the given class
        self.renderer = renderer(self)

    def __str__(self):
        return '[Simulation] Bots: {}'.format(len(bots))

    def update(self):

        if not self.running:
            return

        self.frame += 1
        print('----- frame: {} -----'.format(self.frame))

        status = [(bot.pos, bot.current_goal) for bot in self.bots]

        for bot in self.bots:

            # Move a step if it has one
            bot.update()

            # Output the bot's current status
            bot.print_status()

        new_status = [(bot.pos, bot.current_goal) for bot in self.bots]

        # Nothing has changed, but 
        if (status == new_status):
            for bot in self.bots:
                if not bot.at_goal():
                    print('TRAFFIC JAM!!!!')
                    return
            print('')
            print('=============================================')
            print('Simulation completed successfully!')
            self.stop()
    
    def run(self):

        # Start the loop, this calls update
        self.running = True
        self.renderer.run()

    def stop(self):
        self.running = False

    def resume(self):
        self.running = True
