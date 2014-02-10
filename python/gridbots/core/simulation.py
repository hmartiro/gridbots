"""

"""

import sys
import time
from igraph import Graph, summary

class Simulation:
    """ The overall simulation class. """

    def __init__(self, bots, moves, renderer):

        print 'Welcome to gridbots!'

        self.bots = bots
        self.moves = moves

        # Create a renderer instance from the given class
        self.renderer = renderer(self)

        self.frame = 0

        self.MAP_SIZE = 30.

        self.graph = Graph()
        self.graph.add_vertices(3)
        print self.graph

    def __str__(self):
        return '[Simulation] Bots: {}'.format(len(bots))

    def update(self):

        print '----- frame: {} -----'.format(self.frame)

        for i in range(len(self.bots)):
            self.bots[i].moveX(self.moves[i][self.frame][0])
            self.bots[i].moveY(self.moves[i][self.frame][1])
            print self.bots[i]

        self.renderer.draw()

    def run(self):

        while(True):#self.t < len(self.moves[0])):

            self.update()
            self.frame += 1
