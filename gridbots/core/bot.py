"""

"""

import math
import logging
from operator import itemgetter

import numpy as np
from numpy import linalg

from gridbots.utils.geometry import rotation_between


class Bot:

    """
    Micro robot that has a position in the map and an orientation.

    """

    def __init__(self, name, position, rotation, bot_type, sim):

        self.logger = logging.getLogger(__name__)

        # Bot name
        self.name = str(name)

        # Bot type
        self.type = bot_type

        # Current node
        self.pos = position

        # Last position
        self.last_pos = self.pos

        # Current orientation
        self.rot = rotation

        # Last movement vector (for rotation calc)
        self.last_move_vector = None

        # Save a reference to the simulation
        self.sim = sim

        self.graph = self.sim.map

        # Full history of bot state at each time step
        self.move_history = [self.pos]
        self.rot_history = [self.rot]

    def __repr__(self):
        """ String representation of the bot.
        """
        return '<Bot {}> Type: {}, Position: {}'.format(
            self.name,
            self.type,
            self.pos
        )

    def rotate(self):
        """ Change rotation as needed, based on the current position
            and the move history.
        """

        if not self.move_history:
            return

        n0 = self.move_history[-1]
        n1 = self.pos

        c0 = np.array(itemgetter('x', 'y', 'z')(self.graph.node[n0]))
        c1 = np.array(itemgetter('x', 'y', 'z')(self.graph.node[n1]))

        v0 = self.last_move_vector
        v1 = c1 - c0
        v1 = v1[:2] / linalg.norm(v1[:2])

        # Can't make rotation decision if we have no data
        if v0 is None:
            self.last_move_vector = v1
            return

        # No need to do calculations if movement in same direction
        if (v0 == v1).all():
            return

        v0p = np.array([v0[1], -v0[0]])

        d1 = np.dot(v0, v1)
        d2 = np.dot(v0p, v1)

        # Axis of rotation, whether along v0 or perpendicular to it
        v_rot = v0 if abs(d1) > abs(d2) else v0p

        # Direction
        v_rot = v_rot if d1 > 0 else -v_rot

        theta = rotation_between(v_rot, v1)

        if d1 == 0:
            theta = 0

        if theta > math.pi/2:
            self.logger.warning('v0_u = %s, v1_u = %s', v0, v1)
            self.logger.warning('v_rot = %s, d1 = %s', v_rot, d1)
            self.logger.warning('Rotation theta > pi/2! theta = %s', theta)
            # raise Exception('Invalid rotation, theta = {}'.format(theta))

        self.rot += theta

        self.last_move_vector = v1

    def update(self, control_inputs):
        """
        Given inputs from the controller, update each bot for this time step.
        """

        # Logging header
        # self.logger.debug('################### Bot %s'.format(self.name, self.pos))

        moves_to_make = []

        # TODO return if only waiting

        # Line below is optimized w/ low-level nx access since this is a critical region
        for n2, edge_data in self.graph.adj[self.pos].items():
            for zone in edge_data.keys():
                if zone in control_inputs:
                    if edge_data[zone] == control_inputs[zone]:
                        # self.logger.debug('Bot %s can move from %s to %s'.format(self.name, n1, n2))
                        moves_to_make.append(n2)

        if len(moves_to_make) > 1:
            if len(set(moves_to_make)) != 1:
                raise Exception('Multiple moves possible for bot {}: {}'.format(self.name, moves_to_make))

        if len(moves_to_make) > 0:

            new_pos = moves_to_make[0]
            if new_pos == self.pos:
                raise Exception('Bot {} moving to same node {}!'.format(self.name, self.pos))
            # self.logger.debug('%s, %s, %s'.format(self.pos, new_pos, self.move_history[-5:]))
            self.pos = new_pos
            self.rotate()

        # Record my current position
        self.move_history.append(self.pos)
        self.rot_history.append(self.rot)
