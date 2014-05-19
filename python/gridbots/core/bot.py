"""

"""

from gridbots import utils

import random
import logging
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)


class Bot:
    """
    Micro robot that has a position in the map and an orientation.

    """

    class State():
        """ State definitions of the bot state machine.
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

    def __init__(self, name, position, sim):

        # Bot name
        self.name = str(name)

        # Current node
        self.pos = position

        # Last position
        self.last_pos = self.pos

        # Home position
        self.home_pos = self.pos

        # Current goal node
        self.goal = None

        # Planned path to the goal
        self.moves = []

        # Full trajectory of motion
        self.move_history = []

        # Save a reference to the simulation
        self.sim = sim

        # State machine dictionary
        self.state_machine = {
            Bot.State.at_home: self.state_at_home,
            Bot.State.calculating_path: self.state_calculating_path,
            Bot.State.checking_nodes: self.state_checking_nodes,
            Bot.State.on_track: self.state_on_track,
            Bot.State.finished: self.state_finished,
            Bot.State.traffic_jam: self.state_traffic_jam,
            Bot.State.stuck: self.state_stuck,
        }

        # State variable
        self.state = Bot.State.at_home

        # Whether the robot has made a physical decision to
        # move or wait for the turn
        self.turn_over = False

        # Graph which can have nodes removed for obstacle avoidance
        self.graph = self.sim.map.copy()

        # Check to see if the graph has been modified, to reset it
        self.graph_modified = False

        logging.info('Bot {} initialized at vertex {}.'.format(self.name, self.pos))

    def __repr__(self):
        """ String representation of the bot.
        """
        return '[Bot] Position: {}, Next: {}, State: {}'.format(self.pos, self.moves, self.state)

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
        logging.debug('Moving from {} to {}'.format(self.last_pos, self.pos))

    def wait(self):
        """ Do nothing for this turn.
        """
        self.turn_over = True
        logging.info('Waiting for this turn'.format(self.name))

    def permanent_obstacles(self):
        """ Return a list of bots who are waiting at their home positions.
        """
        return [b.pos for b in self.sim.bots if b.state == Bot.State.at_home]

    def occupied_neighbors(self, node):
        """ Return a list of neighbor nodes that are occupied.
        """
        neighbors = utils.graph.get_neighbors(self.graph, node)
        return [n for n in neighbors if not self.is_node_free(n)]

    def free_neighbors(self, node):
        """ Return a list of neighbor nodes that are free.
        """
        neighbors = utils.graph.get_neighbors(self.graph, node)
        return [n for n in neighbors if self.is_node_free(n)]

    def is_node_free(self, node):
        """ Is the given node occupied by a bot?
        """
        return all([(bot.pos != node) for bot in self.sim.bots if bot is not self])

    def remove_nodes(self, nodes):
        """ Remove the given nodes from my graph.
        """
        self.graph.delete_vertices(self.graph.vs.select(name_in=nodes))

    # -----------------------------------------------------------

    def state_at_home(self):

        logging.debug("State: at_home")

        if self.has_goal():
            return Bot.State.calculating_path
        else:
            self.wait()
            return Bot.State.at_home

    def state_calculating_path(self):

        logging.debug("State: calculating_path")

        # Reset the graph
        self.graph = self.sim.map.copy()

        # List of obstacles
        obstacles = []

        # Neighboring nodes currently occupied
        obstacles.extend(self.occupied_neighbors(self.pos))

        # Bots at their home positions
        obstacles.extend(self.permanent_obstacles())

        # Remove the obstacles from the graph
        self.remove_nodes(obstacles)

        # Go to the goal or towards home position if no goal
        dest_node = self.goal or self.home_pos

        # Get the optimal path to the destination
        if dest_node not in obstacles:
            path = utils.graph.find_shortest_path(self.graph, self.pos, dest_node)

        # If the destination is an obstacle, no path found
        else:
            logging.debug('Destination node is currently an obstacle!')
            path = None

        # If there is a path, we're good to go
        if path:

            self.moves = path[1:]

            # If we have moves
            if self.moves:
                assert self.is_node_free(self.next_move())
                return Bot.State.on_track

            # Otherwise, we should be at the goal
            else:
                assert self.pos == (self.goal or self.home_pos)
                self.goal = None
                return Bot.State.finished

        # Otherwise, check options
        else:
            return Bot.State.checking_nodes

    def state_checking_nodes(self):

        logging.debug("State: checking_nodes")

        # If I am able to move in some direction
        if self.free_neighbors(self.pos):
            return Bot.State.traffic_jam

        # If I am completely stuck
        else:
            return Bot.State.stuck

    def state_on_track(self):

        logging.debug("State: on_track")

        # If the next node is free, go to it
        if self.is_node_free(self.next_move()):

            self.move()

            # Check if I have reached the goal
            if self.has_goal() and self.at_goal():
                return Bot.State.finished

            # Otherwise if no goal, check if I've reached home
            elif not self.has_goal() and self.at_home():
                self.goal = None
                return Bot.State.finished

            # Otherwise, keep moving
            else:
                return Bot.State.on_track

        # I've hit an obstacle, recalculate path
        else:
            return Bot.State.calculating_path

    def state_finished(self):

        logging.debug("State: finished")

        # If I made it home
        if self.at_home():
            return Bot.State.at_home

        # Otherwise, head towards home
        else:
            return Bot.State.calculating_path

    def state_traffic_jam(self):

        logging.debug("State: traffic_jam")

        # Get a list of the free neighboring nodes
        free_neighbors = self.free_neighbors(self.pos)

        # Choose one at random
        random_neighbor = free_neighbors[random.randint(0, len(free_neighbors)-1)]

        # Add it as the path
        self.moves = [random_neighbor]

        # Move to it
        self.move()

        # Recalculate situation
        return Bot.State.calculating_path

    def state_stuck(self):

        logging.debug("State: stuck")

        # If I have any moves, recalculate path
        if self.free_neighbors(self.pos):
            return Bot.State.calculating_path

        # Otherwise, just wait
        else:
            self.wait()
            return Bot.State.stuck

    # -----------------------------------------------------------

    def update(self):
        """ Run the bot state machine until it makes a physical move.
        """

        # Logging header
        logging.info('################### Bot {}'.format(self.name, self.pos))

        # Record my current position
        self.move_history.append(self.pos)

        # Run the state machine until the 'turn' is over
        self.turn_over = False
        while not self.turn_over:
            self.state = self.state_machine[self.state]()

        if self.has_goal():
            logging.info('At {}, moving to goal ({}) with planned moves {}'.format(self.pos, self.goal, self.moves))
        elif self.at_goal():
            logging.info('At goal ({})'.format(self.pos))
        elif not self.at_home():
            logging.info('At {}, moving to home ({}) with planned moves {}'.format(self.pos, self.home_pos, self.moves))
        else:
            logging.info('At home ({})'.format(self.pos))
