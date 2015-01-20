"""

"""

from operator import itemgetter

import logging
import math
import numpy as np
from numpy import linalg


def angle_between(u1, u2):
    """ Returns the angle in radians between vectors 'u1' and 'u2'.
        Assumes the vectors are normalized already.
    """
    angle = np.arccos(np.dot(u1, u2))
    if np.isnan(angle):
        return 0.0 if (u1 == u2).all() else np.pi
    return angle


def angle_from_x(v):
    """ Returns the angle of v from the positive x-axis, 0 to 2 pi.
    """
    assert len(v) == 2
    angle_from_y = -np.arctan2(v[0], v[1])
    if angle_from_y < 0:
        angle_from_y = np.pi + (np.pi + angle_from_y)

    return (angle_from_y + np.pi/2) % (2 * np.pi)


def rotation_between(v1, v2):
    """ Returns the correctly signed rotation in z needed to go
        from v1 to v2 in the XY plane.
    """
    theta = angle_between(v1, v2)
    theta1_x = angle_from_x(v1)
    theta2_x = angle_from_x(v2)
    if theta2_x >= theta1_x:
        sign = +1 if theta2_x - theta1_x < np.pi else -1
    else:
        sign = -1 if theta1_x - theta2_x < np.pi else +1
    return sign * theta


class Bot:

    """
    Micro robot that has a position in the map and an orientation.

    """

    class State():

        """
        State definitions of the bot state machine.

        """

        # Physical states
        at_home = 1
        on_track = 2
        finished = 3
        traffic_jam = 4
        stuck = 5

        # Internal states
        calculating_path = 6
        checking_nodes = 7

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

        # Home position
        self.home_pos = self.pos

        # Current orientation
        self.rot = rotation

        # Last movement vector (for rotation calc)
        self.last_move_vector = None

        # Current goal node
        self.goal = None

        # Planned path to the goal
        self.moves = []

        # Full trajectory of position
        self.move_history = []

        # Full trajectory of orientation
        self.rot_history = []

        # Save a reference to the simulation
        self.sim = sim

        # # State machine dictionary
        # self.state_machine = {
        #     Bot.State.at_home: self.state_at_home,
        #     Bot.State.calculating_path: self.state_calculating_path,
        #     Bot.State.checking_nodes: self.state_checking_nodes,
        #     Bot.State.on_track: self.state_on_track,
        #     Bot.State.finished: self.state_finished,
        #     Bot.State.traffic_jam: self.state_traffic_jam,
        #     Bot.State.stuck: self.state_stuck,
        # }

        # State variable
        self.state = Bot.State.at_home

        # Whether the robot has made a physical decision to
        # move or wait for the turn
        self.turn_over = False

        self.graph = self.sim.map

        # Check to see if the graph has been modified, to reset it
        self.graph_modified = False

        # Is this bot available or assigned to a job?
        self.job = None

    def __repr__(self):
        """ String representation of the bot.
        """
        return '<Bot {}> Type: {}, Position: {}, State: {}, Job: {}'.format(
            self.name,
            self.type,
            self.pos,
            self.state,
            self.job
        )

    def has_move(self):
        """ Do I have a move planned?
        """
        return len(self.moves) > 0

    def next_move(self):
        """ What is my next move?
        """
        return self.moves[0]

    def at_home(self):
        """ Am I at my home position?
        """
        return self.pos == self.home_pos

    def has_goal(self):
        """ Do I have a goal position?
        """
        return self.goal is not None

    def at_goal(self):
        """ Am I at my goal position?
        """
        return self.pos == self.goal

    def assign_goal(self, node):
        """ Set my new goal position, and recalculate my path.
        """
        self.goal = node
        self.state = Bot.State.calculating_path

    def move(self):
        """ Move to my next position.
        """
        self.turn_over = True

        self.last_pos = self.pos
        self.pos = self.moves.pop(0)
        # self.logger.debug('Moving from {} to {}'.format(self.last_pos, self.pos))

    def wait(self):
        """ Do nothing for this turn.
        """
        self.turn_over = True
        # self.logger.debug('Waiting for this turn'.format(self.name))

    def permanent_obstacles(self):
        """ Return a list of bots who are waiting at their home positions.
        """
        return [b.pos for b in self.sim.bots if b.state == Bot.State.at_home]

    def occupied_neighbors(self, node):
        """ Return a list of neighbor nodes that are occupied.
        """
        neighbors = self.graph.neighbors(node)
        return [n for n in neighbors if not self.is_node_free(n)]

    def free_neighbors(self, node):
        """ Return a list of neighbor nodes that are free.
        """
        neighbors = self.graph.neighbors(node)
        return [n for n in neighbors if self.is_node_free(n)]

    def is_node_free(self, node):
        """ Is the given node occupied by a bot?
        """
        return all([(bot.pos != node) for bot in self.sim.bots if bot is not self])

    def remove_nodes(self, nodes):
        """ Remove the given nodes from my graph.
        """
        self.graph.remove_nodes_from(nodes)

    # -----------------------------------------------------------
    #
    # def state_at_home(self):
    #
    #     self.logger.debug("State: at_home")
    #
    #     if self.has_goal():
    #         return Bot.State.calculating_path
    #     else:
    #         self.wait()
    #         return Bot.State.at_home
    #
    # def state_calculating_path(self):
    #
    #     self.logger.debug("State: calculating_path")
    #
    #     # Reset the graph
    #     #self.graph = self.sim.map.copy()
    #
    #     # List of obstacles
    #     obstacles = []
    #
    #     # Neighboring nodes currently occupied
    #     obstacles.extend(self.occupied_neighbors(self.pos))
    #
    #     # Bots at their home positions
    #     obstacles.extend(self.permanent_obstacles())
    #
    #     # Remove the obstacles from the graph
    #     # TODO reincorporate obstacle avoidance
    #     #self.remove_nodes(obstacles)
    #
    #     # Go to the goal or towards home position if no goal
    #     dest_node = self.goal or self.home_pos
    #
    #     # Get the optimal path to the destination
    #     if dest_node not in obstacles:
    #         path = utils.graph.find_shortest_path(self.graph, self.pos, dest_node)
    #
    #     # If the destination is an obstacle, no path found
    #     else:
    #         self.logger.debug('Destination node is currently an obstacle!')
    #         path = None
    #
    #     # If there is a path, we're good to go
    #     if path:
    #
    #         self.moves = path[1:]
    #
    #         # If we have moves
    #         if self.moves:
    #             #assert self.is_node_free(self.next_move())
    #             return Bot.State.on_track
    #
    #         # Otherwise, we should be at the goal
    #         else:
    #             assert self.pos == (self.goal or self.home_pos)
    #             self.goal = None
    #             return Bot.State.finished
    #
    #     # Otherwise, check options
    #     else:
    #         return Bot.State.checking_nodes
    #
    # def state_checking_nodes(self):
    #
    #     self.logger.debug("State: checking_nodes")
    #
    #     # If I am able to move in some direction
    #     if self.free_neighbors(self.pos):
    #         return Bot.State.traffic_jam
    #
    #     # If I am completely stuck
    #     else:
    #         return Bot.State.stuck
    #
    # def state_on_track(self):
    #
    #     self.logger.debug("State: on_track")
    #
    #     # If the next node is free, go to it
    #     # TODO reincorporate obstacle avoidance
    #     if self.is_node_free(self.next_move()) or True:
    #
    #         self.move()
    #
    #         # Check if I have reached the goal
    #         if self.has_goal() and self.at_goal():
    #             return Bot.State.finished
    #
    #         # Otherwise if no goal, check if I've reached home
    #         elif not self.has_goal() and self.at_home():
    #             return Bot.State.finished
    #
    #         # Otherwise, keep moving
    #         else:
    #             return Bot.State.on_track
    #
    #     # I've hit an obstacle, recalculate path
    #     else:
    #         return Bot.State.calculating_path
    #
    # def state_finished(self):
    #
    #     self.logger.debug("State: finished")
    #
    #     # If I made it home
    #     if self.at_home():
    #         return Bot.State.at_home
    #
    #     # Otherwise, see if i'm doing an operation
    #     else:
    #         return Bot.State.calculating_path
    #
    # def state_traffic_jam(self):
    #
    #     self.logger.debug("State: traffic_jam")
    #
    #     # Get a list of the free neighboring nodes
    #     free_neighbors = self.free_neighbors(self.pos)
    #
    #     # Choose one at random
    #     random_neighbor = free_neighbors[random.randint(0, len(free_neighbors)-1)]
    #
    #     # Add it as the path
    #     self.moves = [random_neighbor]
    #     #self.moves = [free_neighbors[-1]]
    #
    #     # Move to it
    #     self.move()
    #
    #     # Recalculate situation
    #     return Bot.State.calculating_path
    #
    # def state_stuck(self):
    #
    #     self.logger.debug("State: stuck")
    #     self.logger.debug('neighbors: %s'.format(self.free_neighbors(self.pos)))
    #     # If I have any moves, recalculate path
    #     # if self.free_neighbors(self.pos):
    #     #     return Bot.State.calculating_path
    #     #
    #     # # Otherwise, just wait
    #     # else:
    #     self.wait()
    #     return Bot.State.calculating_path

    # -----------------------------------------------------------

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

    def update(self):
        """ Run the bot state machine until it makes a physical move.
        """

        # Logging header
        # self.logger.debug('################### Bot %s'.format(self.name, self.pos))

        # Record my current position
        self.move_history.append(self.pos)
        self.rot_history.append(self.rot)

        moves_to_make = []

        # Line below is optimized w/ low-level nx access since this is a critical region
        for n2, edge_data in self.graph.adj[self.pos].items():
            for zone in edge_data.keys():
                if zone in self.sim.control_inputs:
                    if edge_data[zone] == self.sim.control_inputs[zone]:
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
