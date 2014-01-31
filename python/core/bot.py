"""

Gridbots plan:

Inputs:
- File describing the terrain
- File describing the initial positions
- File describing the goal positions

Outputs:
- Paths of each robot
- Visualization

"""

import math
import pygame

def enum(**enums):
    return type('Enum', (), enums)

Orientation = enum(
        N=0*math.pi/2., 
        S=1*math.pi/2., 
        E=2*math.pi/2., 
        W=3*math.pi/2.
    )

class Bot:
    """ A little robot that can translate and rotate. """

    def __init__(self, x, y, orientation):

        self.x = x
        self.y = y
        self.orientation = orientation

    def __str__(self):
        return '[Bot] Pos: ({}, {}), Orientation: {}'.format(self.x, self.y, self.orientation)

    def moveX(self, dx):
        self.x += dx

    def moveY(self, dy):
        self.y += dy

    def rotate(self, rad):
        self.orientation += rad

    def render(self, screen):
        pygame.draw.circle(screen, (255,0,0), (self.x, self.y), 10)
