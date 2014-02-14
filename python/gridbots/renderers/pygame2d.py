
import sys
import math
import numpy
import pygame

from gridbots.utils.vec2d import Vec2d

# Screen width in pixels
SCREEN_WIDTH = 600

# Fraction of map size to show as margin
MARGIN = 0.2

# Simulation framerate
FRAMERATE = 6
REDRAW_SUBSTEPS = 10

# Drawing colors
BG_COLOR = (100, 100, 100)
ROBOT_COLOR = (255, 255, 255)
INNER_ROBOT_COLOR = (50, 50, 50)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

###############################

def linmap(val, inMin, inMax, outMin, outMax):
    """
    Simple linear mapping utility.
    """
    return (val-inMin)/(inMax-inMin) * (outMax-outMin) + outMin

###############################

class PyGameDrawer():
    
    def __init__(self, sim):

        # Reference to the simulation object
        self.sim = sim

        # Initialize the pygame library
        pygame.init()

        # Get map dimensions
        self.minX = self.sim.map_dimensions[0]
        self.maxX = self.sim.map_dimensions[1]
        self.minY = self.sim.map_dimensions[2] 
        self.maxY = self.sim.map_dimensions[3]

        # Calculate screen width based on the map proportions
        self.width = SCREEN_WIDTH
        self.height = self.width * (self.maxY - self.minY) / (self.maxX - self.minX)

        # Add some room for margins
        self.margin = SCREEN_WIDTH * MARGIN / 2
        self.full_width = int(self.width + self.margin * 2)
        self.full_height = int(self.height + self.margin * 2)

        # Set pygame screen width
        self.screen = pygame.display.set_mode((self.full_width, self.full_height), 0, 32)

        # Create clock to count frames
        self.clock = pygame.time.Clock()

    def to_pixel(self, coord):

        px = linmap(coord[0], self.minX, self.maxX, self.margin, self.width + self.margin)
        py = linmap(coord[1], self.minY, self.maxY, self.height + self.margin, self.margin)

        return (int(px), int(py))

    def scale(self, coord):

        sx = coord[0] * self.width / (self.maxX - self.minX)
        sy = coord[1] * self.height / (self.maxY - self.minY)

        return (int(sx), int(sy))

    def draw_rect(self, center, size, color, width=0):

        # Calculate pixel corner and rectangle size
        top_left = (center[0] - size[0]/2, center[1] + size[1]/2)
        p_top_left = self.to_pixel(top_left)
        p_size = self.scale(size)

        # Draw the rectangle
        rect = pygame.Rect(p_top_left[0], p_top_left[1], p_size[0], p_size[1])
        pygame.draw.rect(self.screen, color, rect, width)

    def draw_circle(self, center, radius, color, width=0):

        # Calculate center
        p_center = self.to_pixel(center)

        # Calculate radius
        p_radius = self.scale((radius, radius))[0]

        # Draw the circle
        pygame.draw.circle(self.screen, color, p_center, p_radius)

    def draw_line(self, start, end, color, width=1):

        # Calculate pixel coordinates
        p_start = self.to_pixel(start)
        p_end = self.to_pixel(end)

        # Draw the line
        pygame.draw.line(self.screen, color, p_start, p_end, width)

    def draw(self):

        # Check for events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()

        # Instead of drawing one frame with the robot, interpolate
        # between the old and new robot positions so the simulation
        # plays a smooth movement
        for t in range(REDRAW_SUBSTEPS):

            # Redraw the background
            self.screen.fill(BG_COLOR)
            
            # Draw the map components
            self.draw_map()

            for bot in self.sim.bots:
                fraction = float(t+1)/REDRAW_SUBSTEPS
                self.draw_bot(bot, fraction)

            pygame.display.flip()

            self.clock.tick(FRAMERATE * REDRAW_SUBSTEPS)

    def draw_map(self):

        # Draw the map outer limits
        #center = (numpy.mean([self.minX, self.maxX]), numpy.mean([self.minY, self.maxY]))
        #size = (self.maxX - self.minX, self.maxY - self.minY)
        #self.draw_rect(center, size, (150, 150, 150), width=2)

        for v in self.sim.graph.vs:
           self.draw_circle(v["coords"], 0.1, BLACK)

        for e in self.sim.graph.es:
            source = self.sim.graph.vs[e.source]["coords"]
            target = self.sim.graph.vs[e.target]["coords"]
            self.draw_line(source, target, BLACK, width=2)

    def draw_bot(self, bot, fraction):

        # Get the old and new positions of the robot
        c1 = self.sim.graph.vs[bot.last_pos]["coords"]
        c2 = self.sim.graph.vs[bot.pos]["coords"]

        # Interpolate based on the fraction
        coords = [linmap(fraction, 0, 1, c1[0], c2[0]), linmap(fraction, 0, 1, c1[1], c2[1])]

        # Draw!
        self.draw_rect(coords, (0.5, 0.5), ROBOT_COLOR)
        self.draw_rect(coords, (0.25, 0.25), INNER_ROBOT_COLOR)

    def run(self):

        while(True):

            # Update simulation
            self.sim.update()

            # Draw everything
            self.draw()

    def quit(self):
        sys.exit()
