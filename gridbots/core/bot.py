"""

"""

from gridbots import utils

import random
import logging


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

    def __init__(self, name, position, bot_type, sim):

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
        self.logger.debug('Moving from {} to {}'.format(self.last_pos, self.pos))

    def wait(self):
        """ Do nothing for this turn.
        """
        self.turn_over = True
        self.logger.info('Waiting for this turn'.format(self.name))

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

    def state_at_home(self):

        self.logger.debug("State: at_home")

        if self.has_goal():
            return Bot.State.calculating_path
        else:
            self.wait()
            return Bot.State.at_home

    def state_calculating_path(self):

        self.logger.debug("State: calculating_path")

        # Reset the graph
        #self.graph = self.sim.map.copy()

        # List of obstacles
        obstacles = []

        # Neighboring nodes currently occupied
        obstacles.extend(self.occupied_neighbors(self.pos))

        # Bots at their home positions
        obstacles.extend(self.permanent_obstacles())

        # Remove the obstacles from the graph
        # TODO reincorporate obstacle avoidance
        #self.remove_nodes(obstacles)

        # Go to the goal or towards home position if no goal
        dest_node = self.goal or self.home_pos

        # Get the optimal path to the destination
        if dest_node not in obstacles:
            path = utils.graph.find_shortest_path(self.graph, self.pos, dest_node)

        # If the destination is an obstacle, no path found
        else:
            self.logger.debug('Destination node is currently an obstacle!')
            path = None

        # If there is a path, we're good to go
        if path:

            self.moves = path[1:]

            # If we have moves
            if self.moves:
                #assert self.is_node_free(self.next_move())
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

        self.logger.debug("State: checking_nodes")

        # If I am able to move in some direction
        if self.free_neighbors(self.pos):
            return Bot.State.traffic_jam

        # If I am completely stuck
        else:
            return Bot.State.stuck

    def state_on_track(self):

        self.logger.debug("State: on_track")

        # If the next node is free, go to it
        # TODO reincorporate obstacle avoidance
        if self.is_node_free(self.next_move()) or True:

            self.move()

            # Check if I have reached the goal
            if self.has_goal() and self.at_goal():
                return Bot.State.finished

            # Otherwise if no goal, check if I've reached home
            elif not self.has_goal() and self.at_home():
                return Bot.State.finished

            # Otherwise, keep moving
            else:
                return Bot.State.on_track

        # I've hit an obstacle, recalculate path
        else:
            return Bot.State.calculating_path

    def state_finished(self):

        self.logger.debug("State: finished")

        # If I made it home
        if self.at_home():
            return Bot.State.at_home

        # Otherwise, see if i'm doing an operation
        else:
            return Bot.State.calculating_path

    def state_traffic_jam(self):

        self.logger.debug("State: traffic_jam")

        # Get a list of the free neighboring nodes
        free_neighbors = self.free_neighbors(self.pos)

        # Choose one at random
        random_neighbor = free_neighbors[random.randint(0, len(free_neighbors)-1)]

        # Add it as the path
        self.moves = [random_neighbor]
        #self.moves = [free_neighbors[-1]]

        # Move to it
        self.move()

        # Recalculate situation
        return Bot.State.calculating_path

    def state_stuck(self):

        self.logger.debug("State: stuck")
        print('neighbors: {}'.format(self.free_neighbors(self.pos)))
        # If I have any moves, recalculate path
        # if self.free_neighbors(self.pos):
        #     return Bot.State.calculating_path
        #
        # # Otherwise, just wait
        # else:
        self.wait()
        return Bot.State.calculating_path

    # -----------------------------------------------------------

    def update(self):
        """ Run the bot state machine until it makes a physical move.
        """

        # Logging header
        self.logger.info('################### Bot {}'.format(self.name, self.pos))

        # Record my current position
        self.move_history.append(self.pos)

        # Run the state machine until the 'turn' is over
        self.turn_over = False
        while not self.turn_over:
            self.state = self.state_machine[self.state]()

        # Log state information
        if self.has_goal():
            self.logger.info('At {}, moving to goal ({}) in {} more moves'.format(
                self.pos, self.goal, len(self.moves)))
        elif self.at_goal():
            self.logger.info('At goal ({})'.format(self.pos))
        elif not self.at_home():
            self.logger.info('At {}, moving to home ({}) in {} more moves'.format(
                self.pos, self.home_pos, len(self.moves)))
        else:
            self.logger.info('At home ({})'.format(self.pos))

        # Move based on routine
        # TODO temporary
        routine = self.sim.routines['units1_2_tree_int']
        move_dict = routine[self.sim.frame]
        print(move_dict)

        out_edges = self.graph.out_edges(self.pos, data=True)
        moves_to_make = []
        for n1, n2, edge_data in out_edges:
            for zone in edge_data.keys():
                if zone in move_dict:
                    if edge_data[zone] == move_dict[zone]:
                        print('Bot {} can move from {} to {}'.format(self.name, n1, n2))
                        moves_to_make.append(n2)

        print('Possible moves: {}'.format(moves_to_make))
        if len(moves_to_make) > 0:
            self.pos = moves_to_make[0]

        if len(moves_to_make) > 1:
            raise Exception()
