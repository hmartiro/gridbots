
import sys
import pygame

from gridbots.utils.vec2d import Vec2d

SCREEN_SIZE = 600

BG_COLOR = (100, 100, 100)
ROBOT_COLOR = (255, 255, 255)
INNER_ROBOT_COLOR = (50, 50, 50)

FRAMERATE = 2

class PyGameDrawer():
    
    def __init__(self, sim):

        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE), 0, 32)
        self.clock = pygame.time.Clock()

        # Reference to the simulation object
        self.sim = sim

    def to_pixel(self, x, y):

        px = (0.5 + x/self.sim.MAP_SIZE) * SCREEN_SIZE 
        py = (0.5 - y/self.sim.MAP_SIZE) * SCREEN_SIZE

        return (int(px), int(py))

    def draw(self):

        # Check for events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()

        # Redraw the background
        self.screen.fill(BG_COLOR)
        
        for bot in self.sim.bots:
            self.draw_bot(bot)

        pygame.display.flip()

        self.clock.tick(FRAMERATE)

    def draw_bot(self, bot):

        coords = self.to_pixel(bot.x, bot.y)

        size = SCREEN_SIZE/self.sim.MAP_SIZE

        rect = pygame.Rect(coords[0], coords[1], size, size)
        pygame.draw.rect(self.screen, ROBOT_COLOR, rect)

        rect = pygame.Rect(size/4 + coords[0], size/4 + coords[1], size/2, size/2)
        pygame.draw.rect(self.screen, INNER_ROBOT_COLOR, rect)

    def quit(self):
        sys.exit()
