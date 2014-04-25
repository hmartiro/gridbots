"""

"""

import math
from collections import deque

class Bot:
    """
    Micro robot that has a position in the map and an orientation.

    """

    # Dictionary of robot orientations
    ORIENTATION = {
            'N': 0*math.pi/2., 
            'S': 1*math.pi/2., 
            'E': 2*math.pi/2., 
            'W': 3*math.pi/2.
        }

    def __init__(self, name, position, orientation, sim):

        # What is my name
        self.name = str(name)

        # Which vertex am I at?
        self.pos = position

        # Which way am I pointing?
        self.orientation = self.ORIENTATION[orientation]

        # What are my next moves?
        self.move_queue = deque()

        # What are my pending goals?
        self.goal_queue = deque()

        # Where am I currently going?
        self.current_goal = self.pos

        # Where was my last position?
        self.last_pos = self.pos

        # Save a reference to the simulation
        self.sim = sim

        print('Bot {} initialized at vertex {}.'.format(self.name, self.pos))

    def __repr__(self):
        return '[Bot] Position: {}, Next: {}'.format(self.pos, self.move_queue)

    def add_goal(self, new_goal_position):
        self.goal_queue.append(new_goal_position)

    def has_goal(self):
        return len(self.goal_queue) != 0
    
    def pop_goal(self):

        self.current_goal = self.goal_queue.popleft()
        return self.current_goal

    def add_move(self, new_position):
        self.move_queue.append(new_position)

    def has_move(self):
        return len(self.move_queue) != 0

    def at_goal(self):

        at_goal = (self.pos == self.current_goal)

        if at_goal:
            assert not self.has_move()

        return at_goal

    def is_free(self, node):
        """
        Is the given node currently unoccupied?

        """

        for bot in self.sim.bots:

            if(bot.pos == node):
                return False

        return True

    def rotate(self, rad):
        self.orientation += rad

    def plan_path(self, graph, current, goal):
        """
        Given a graph, a starting node, and a goal node,
        calculate the shortest path and add it to the move
        queue.

        """

        src = graph.vs.select(name=current)[0]
        target = graph.vs.select(name=goal)[0]

        move_ids = graph.get_shortest_paths(src, to=target)
        moves = [graph.vs[m]["name"] for m in move_ids[0]]

        self.move_queue = deque()
        for move in moves[1:]:
            self.add_move(move)

        return moves

    def update(self):

        # If the bot has reached its goal
        if self.at_goal():

            # If there are more goals
            if self.has_goal():

                # Get the next one
                goal = self.pop_goal()

                # Calculate the shortest path to the goal
                moves = self.plan_path(self.sim.graph, self.pos, goal)
                print moves

        self.last_pos = self.pos
        print self.move_queue

        if not self.has_move():
            return
        
        p = self.move_queue.popleft()
        
        if self.is_free(p):
            self.pos = p
        else:
            print('bot {} says node {} is occupied!'.format(self.name, p))

            # Get graph without the offending point
            g2 = self.sim.graph.copy()

            # Get all neighbors of my current position
            neighbors = self.sim.graph.vs.select(name=self.pos)[0].neighbors()

            # Find which neighbors are occupied
            occupied_neighbors = []
            for n in neighbors:
                if not self.is_free(n["name"]):
                    occupied_neighbors.append(n["name"])

            print("Occupied neighbors of {}: {}".format(self.pos, occupied_neighbors))

            g2.delete_vertices(occupied_neighbors)

            old_move_queue = self.move_queue

            # Calculate shortest path
            moves = self.plan_path(g2, self.pos, self.current_goal)

            #print old_move_queue, self.move_queue

            # Move!
            self.pos = self.move_queue.popleft()  

    def print_status(self):

        # If I still have moves
        if self.has_move():
            print('Bot {} is at vertex {}, reaching goal of {} in {} moves.'.format(self.name, self.pos, self.current_goal, len(self.move_queue)))

        # If I am at my goal
        if self.at_goal():
            print('Bot {} is at goal of vertex {}!'.format(self.name, self.pos))
    