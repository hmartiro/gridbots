"""

"""

import sys
import math
import yaml
import pygame

from gridbots.utils.graph import read_graph
from gridbots.utils.graph import get_bounding_box

# Screen width in pixels
SCREEN_WIDTH = 600

# Fraction of map size to show as margin
MARGIN = 0.2

# Simulation framerate
FRAMERATE = 15
REDRAW_SUBSTEPS = 3

# Drawing colors
BG_COLOR = (100, 100, 100)
LIGHT_GRAY = (200, 200, 200)
INNER_ROBOT_COLOR = (50, 50, 50)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

###############################

def linmap(val, inMin, inMax, outMin, outMax):
    """
    Simple linear mapping utility.
    """
    return (val-inMin)/(inMax-inMin) * (outMax-outMin) + outMin

###############################

class PyGameDrawer():
    
    def __init__(self, paths_name, framerate=FRAMERATE, substeps=REDRAW_SUBSTEPS):

        # Read the paths file
        paths_file ='paths/{}.yml'.format(paths_name)
        with open(paths_file) as pf:
            paths_data = yaml.load(pf.read())

        self.bots = paths_data["bots"]

        self.map = read_graph("maps/{}.yml".format(paths_data["map_name"]))

        self.frames = paths_data["frames"]

        self.framerate = framerate
        self.substeps = substeps

        # Get map dimensions
        self.bounding_box = get_bounding_box(self.map)
        self.minX = self.bounding_box[0]
        self.maxX = self.bounding_box[1]
        self.minY = self.bounding_box[2] 
        self.maxY = self.bounding_box[3]

        # Initialize the pygame library
        pygame.init()

        # Calculate screen width based on the map proportions
        self.width = SCREEN_WIDTH
        self.height = self.width * (self.maxY - self.minY) / (self.maxX - self.minX)

        self.scaling = math.sqrt((self.maxY - self.minY) * (self.maxX - self.minX))

        # Add some room for margins
        self.margin = SCREEN_WIDTH * MARGIN / 2
        self.full_width = int(self.width + self.margin * 2)
        self.full_height = int(self.height + self.margin * 2)

        # Set pygame screen width
        self.screen = pygame.display.set_mode((self.full_width, self.full_height), 0, 32)

        # Title
        pygame.display.set_caption('Gridbots!')

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

    def draw_circle(self, center, radius, color, width=0.):

        # Calculate center
        p_center = self.to_pixel(center)

        # Calculate radius
        radius *= math.pow(self.scaling / 10., .8)
        p_radius = self.scale((radius, radius))[0]

        # Calculate width
        width *= math.pow(self.scaling / 10., .8)
        p_width = self.scale((width, width))[0]
        if ((width > 0) and (p_width == 0)):
            p_width = 1

        # Draw the circle
        pygame.draw.circle(self.screen, color, p_center, p_radius, p_width)

    def draw_line(self, start, end, color, width=1):

        # Calculate pixel coordinates
        p_start = self.to_pixel(start)
        p_end = self.to_pixel(end)

        # Draw the line
        pygame.draw.line(self.screen, color, p_start, p_end, width)

    def draw_text(self, coords, text, size=.5, color=BLACK, font=None):

        size *= math.pow(self.scaling / 10., .8)
        p_size = self.scale((size, size))[0]

        fontObj = pygame.font.Font(font, p_size)
        textSurfaceObj = fontObj.render(text, True, color)
        textRectObj = textSurfaceObj.get_rect()
        textRectObj.center = self.to_pixel(coords)

        self.screen.blit(textSurfaceObj, textRectObj)

    def draw(self, frame):

        # Check for events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        self.clock.tick(self.framerate * self.substeps)

        if frame < 0:
            return

        # Instead of drawing one frame with the robot, interpolate
        # between the old and new robot positions so the simulation
        # plays a smooth movement
        for t in range(self.substeps):

            # Redraw the background
            self.screen.fill(BG_COLOR)
            
            # Draw the map components
            self.draw_map()

            for bot in self.bots.keys():
                fraction = float(t+1)/self.substeps
                self.draw_bot(bot, fraction, frame)

            pygame.display.flip()

    def draw_map(self):

        for e in self.map.es:
            source = self.map.vs[e.source]["coords"]
            target = self.map.vs[e.target]["coords"]
            self.draw_line(source, target, BLACK, width=2)

        for v in self.map.vs:
            self.draw_circle(v["coords"], 0.3, BLACK)
            self.draw_text(v["coords"], str(v["name"]), size=0.45, color=WHITE)

    def draw_bot(self, bot, fraction, frame):

        last_node = self.bots[bot][frame]
        current_node = self.bots[bot][frame+1]

        # Get the old and new positions of the robot
        c1 = self.map.vs.select(name=last_node)[0]["coords"]
        c2 = self.map.vs.select(name=current_node)[0]["coords"]

        # Interpolate based on the fraction
        coords = [linmap(fraction, 0, 1, c1[0], c2[0]), linmap(fraction, 0, 1, c1[1], c2[1])]

        # Draw!
        radius = 0.50
        self.draw_circle(coords, radius, LIGHT_GRAY)
        self.draw_circle(coords, radius + 0.02, BLACK, width=0.04)

        size = 0.90
        self.draw_text(coords, bot, size=size, color=BLACK)

    def run(self):
        
        for frame in range(self.frames):

            # Draw everything
            self.draw(frame)

        while True:
            self.draw(-1)
