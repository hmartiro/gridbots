"""

"""

import math
import logging
from operator import itemgetter

import mathutils as mu


class Bot:
    """
    Micro robot that has a position in the map and an orientation.

    """

    logger = logging.getLogger(__name__)

    def __init__(self, name, node, rotation, bot_type, graph):

        # Bot name
        self.name = str(name)

        # Bot type
        self.type = bot_type

        # Current node
        self.node = node

        # Last movement vector (for rotation calc)
        self.last_move_vector = None

        # Save a reference to the simulation
        self.graph = graph

        # Handy for getting the position from the node
        # self.xyz_getter(self.graph.node[self.node])
        self.xyz_getter = itemgetter('x', 'y', 'z')

        # Position (coordinates)
        # Directly calculable from the current node
        self.pos = self.node_to_pos(self.node)
        self.last_pos = None

        # Current orientation
        self.rot = rotation

        # Full history of bot state at each time step
        self.move_history = [self.node]
        self.rot_history = [self.rot]

        self.last_pos = None

    def node_to_pos(self, node):
        return mu.Vector(self.xyz_getter(self.graph.node[self.node])) * 24

    def __repr__(self):
        """ String representation of the bot.
        """
        return '<Bot {}> Type: {}, Position: {}'.format(
            self.name,
            self.type,
            self.node
        )

    def rotate(self):
        """ Change rotation as needed, based on the current position
            and the move history.
        """

        if not self.last_pos:
            return

        c0 = self.last_pos
        c1 = self.pos

        v0 = self.last_move_vector
        v1 = c1 - c0
        v1 = mu.Vector([v1.x, v1.y, 0]).normalized()

        # Can't make rotation decision if we have no data
        if v0 is None:
            self.last_move_vector = v1
            return

        # No need to do calculations if movement in same direction
        if v0 == v1:
            return

        v0p = mu.Vector([v0.y, -v0.x, 0])

        d1 = v0.dot(v1)
        d2 = v0p.dot(v1)

        # Axis of rotation, whether along v0 or perpendicular to it
        v_rot = v0 if abs(d1) > abs(d2) else v0p

        # Direction
        v_rot = v_rot if d1 > 0 else -v_rot

        theta = v_rot.rotation_difference(v1).to_euler().z

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
        # self.logger.debug('################### Bot %s'.format(self.name, self.node))

        moves_to_make = []

        # TODO return if only waiting

        # Line below is optimized w/ low-level nx access since this is a critical region
        for n2, edge_data in self.graph.adj[self.node].items():
            for zone in edge_data.keys():
                if zone in control_inputs:
                    if edge_data[zone] == control_inputs[zone]:
                        # self.logger.debug('Bot %s can move from %s to %s'.format(self.name, n1, n2))
                        moves_to_make.append(n2)

        if len(moves_to_make) > 1:
            if len(set(moves_to_make)) != 1:
                raise Exception('Multiple moves possible for bot {}: {}'.format(self.name, moves_to_make))

        if len(moves_to_make) > 0:

            new_node = moves_to_make[0]
            if new_node == self.node:
                raise Exception('Bot {} moving to same node {}!'.format(self.name, self.node))

            self.node = new_node
            self.last_pos = self.pos
            self.pos = self.node_to_pos(self.node)
            self.rotate()

        # Record my current position
        #self.move_history.append(self.node)
        #self.rot_history.append(self.rot)
