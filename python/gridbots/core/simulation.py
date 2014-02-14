"""

"""

import yaml

from igraph import Graph, summary, plot

from gridbots.core.bot import Bot

class Simulation:
    """ The overall simulation class. """

    def __init__(self, map_filename, renderer):

        print('Welcome to gridbots!')

        # Read the map file
        with open(map_filename) as map_file:
            map_data = yaml.load(map_file.read())
        print map_data

        # Extract data from the yaml
        self.map_name = map_data['name']
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

        print('----- Creating bots -----')
        # List of bots in the simulation
        self.bots = []

        # Iterate through the input file and create bots
        for bot_name, bot_data in map_data['bots'].items():

            # Create a bot
            bot = Bot(
                    name=bot_name,
                    position=bot_data['position'],
                    orientation=bot_data['orientation']
                )

            # Queue all goal positions
            for vertex in bot_data['goals']:
                bot.add_goal(vertex)

            # Add it to our list
            self.bots.append(bot)

        self.graph = Graph(len(vertices))
        self.graph.add_edges(edges)

        for v_id, v_coord in vertices:
            self.graph.vs[v_id]["coords"] = v_coord

        # Count frames
        self.frame = 0

        # Create a renderer instance from the given class
        self.renderer = renderer(self)

        # Start the loop, this calls update
        self.renderer.run()

    def __str__(self):
        return '[Simulation] Bots: {}'.format(len(bots))

    def update(self):

        self.frame += 1
        print('----- frame: {} -----'.format(self.frame))

        for bot in self.bots:

            # If the bot has reached its goal
            if bot.at_goal():

                # If there are more goals
                if bot.has_goal():

                    # Get the next one
                    goal = bot.pop_goal()

                    # Calculate the shortest path to the goal
                    moves = self.graph.get_shortest_paths(bot.pos, to=goal)

                    # Add these as moves for the bot
                    for move in moves[0][1:]:
                        bot.add_move(move)

            # Move a step if it has one
            bot.update()

            # Output the bot's current status
            bot.print_status()
