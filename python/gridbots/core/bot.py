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

        # What has been my entire trajectory?
        self.move_history = []

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

    def get_obstacles(self):

        finished_bots = []
        for bot in self.sim.bots:
            if bot.at_goal() and not bot.has_goal():
                finished_bots.append(bot.pos)

        return finished_bots

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

        self.move_history.append(self.pos)

        # If the bot has reached its goal
        if self.at_goal():

            # If there are more goals
            if self.has_goal():

                # Get the next one
                goal = self.pop_goal()

                # Calculate the shortest path to the goal
                moves = self.plan_path(self.sim.graph, self.pos, goal)
                print(moves)

        self.last_pos = self.pos
        #print self.move_queue

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
            neighbors = [n["name"] for n in self.sim.graph.vs.select(name=self.pos)[0].neighbors()]

            # Find which neighbors are occupied
            occupied_neighbors = []
            for n in neighbors:
                if not self.is_free(n):
                    occupied_neighbors.append(n)

            print("Neighbors of {}: {}. Occupied: {}".format(self.pos, neighbors, occupied_neighbors))

            # Check if path is completely blocked
            if occupied_neighbors == neighbors:
                self.move_queue.appendleft(p)
                print('Completely trapped, waiting!')
                return 

            g2.delete_vertices(g2.vs.select(name_in=occupied_neighbors))

            obstacles = self.get_obstacles()
            g2.delete_vertices(g2.vs.select(name_in=obstacles))

            print("Deleting nodes {} because bots are at goals".format(obstacles))
            
            # Check if goal is still in the graph
            if self.current_goal in occupied_neighbors:
                #print('{} not found in graph, deleted {}!'.format(self.current_goal, occupied_neighbors))
                self.move_queue.appendleft(p)
                return

            old_move_queue = self.move_queue

            # Calculate shortest path
            print('source: {}, dest: {}'.format(self.pos, self.current_goal))
            moves = self.plan_path(g2, self.pos, self.current_goal)

            print(old_move_queue, self.move_queue)

            # Move!
            self.pos = self.move_queue.popleft()  

    def print_status(self):

        # If I still have moves
        if self.has_move():
            print('Bot {} is at vertex {}, reaching goal of {} in {} moves.'.format(self.name, self.pos, self.current_goal, len(self.move_queue)))

        # If I am at my goal
        if self.at_goal():
            print('Bot {} is at goal of vertex {}!'.format(self.name, self.pos))
    