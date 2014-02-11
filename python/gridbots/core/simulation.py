"""

"""

import yaml

from igraph import Graph, summary, plot

from gridbots.core.bot import Bot, Orientation

class Simulation:
    """ The overall simulation class. """

    def __init__(self, map_filename, moves, renderer):

        print 'Welcome to gridbots!'

        # Read the map file
        with open(map_filename) as map_file:
            map_data = yaml.load(map_file.read())
        print map_data
        
        # Extract data from the yaml
        self.map_name = map_data['name']
        vertices = map_data['vertices']
        edges = map_data['edges']
        
        min_x = min_y = float("+inf")
        max_x = max_y = float("-inf")
        for v in vertices.values():
            if v[0] > max_x:
                max_x = v[0]
            if v[0] < min_x:
                min_x = v[0]
            if v[1] > max_y:
                max_y = v[1]
            if v[1] < min_y:
                min_y = v[1]
        self.map_dimensions = (min_x, max_x, min_y, max_y)

        # Create bots
        self.bots = []
        for bot_name in map_data['bots']:
            coords = vertices[map_data['bots'][bot_name]]
            bot = Bot(x=coords[0], y=coords[1], orientation=Orientation.N)
            self.bots.append(bot)

        print 'Vertices: {}'.format(vertices)
        print 'Edges: {}'.format(edges)
        print 'Bots: {}'.format(self.bots)

        self.graph = Graph(len(vertices))
        self.graph.add_edges(edges)

        self.graph.vs["coords"] = vertices.values()

        #print self.graph.es[1].target
        #layout = self.graph.layout("kk")
        #plot(self.graph, layout=layout)

        self.moves = moves

        # Create a renderer instance from the given class
        self.renderer = renderer(self)

        self.frame = 0

    def __str__(self):
        return '[Simulation] Bots: {}'.format(len(bots))

    def update(self):

        print '----- frame: {} -----'.format(self.frame)

        self.renderer.draw()

        if(self.frame < len(self.moves[0])):
            for i in range(len(self.bots)):
                self.bots[i].moveX(self.moves[i][self.frame][0])
                self.bots[i].moveY(self.moves[i][self.frame][1])
                print self.bots[i]

    def run(self):

        while(True):

            self.update()
            self.frame += 1