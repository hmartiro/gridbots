"""

"""


class SingleRoutineConroller():

    def __init__(self, bots, sim_map, routine):
        self.bots = bots
        self.map = sim_map
        self.routine = routine
        self.finished = False

    def step(self, frame):

        if frame >= len(self.routine) * 1:
            self.finished = True
            return

        return self.routine[frame % len(self.routine)]
