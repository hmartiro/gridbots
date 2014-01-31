"""

"""

import sys
import time
import pygame

SCREEN_SIZE = (400, 400)
BG_COLOR = (100, 200, 200)

class Simulation:
    """ The overall simulation class. """

    def __init__(self, bots, moves):

        print 'Welcome to gridbots!'

        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE, 0, 32)
        self.clock = pygame.time.Clock()

        self.bots = bots
        self.moves = moves

        self.frame = 0

    def __str__(self):
        return '[Simulation] Bots: {}'.format(len(bots))

    def update(self):

        print '----- frame: {} -----'.format(self.frame)

        # Check for events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()
        
        # Redraw the background
        self.screen.fill(BG_COLOR)
        
        for bot in self.bots:
            bot.render(self.screen)

        pygame.display.flip()

        for i in range(len(self.bots)):
            #self.bots[i].moveX(self.moves[i][self.t][0])
            #self.bots[i].moveY(self.moves[i][self.t][1])
            print self.bots[i]

        time_passed = self.clock.tick(2)

    def run(self):

        while(True):#self.t < len(self.moves[0])):

            self.update()
            self.frame += 1

    def quit(self):
        sys.exit()
