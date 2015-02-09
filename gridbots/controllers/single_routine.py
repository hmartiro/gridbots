"""

"""

import os
import gridbots
from gridbots.core.routine import TrajectoryBuilder


class RoutineController():

    def __init__(self, sim, options):

        self.sim = sim
        self.bots = self.sim.bots

        self.routine_name = options['routine']
        self.finished = False

        script_dir = os.path.join(gridbots.path, 'sri-scripts')
        builder = TrajectoryBuilder(script_dir, self.routine_name)
        self.routine = builder.moves

    def step(self, frame):

        if frame >= len(self.routine):
            self.finished = True
            return {}

        return self.routine[frame]
