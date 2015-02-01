"""

"""


class Structure:

    def __init__(self, graph):

        self.x = 0
        self.y = 0
        self.z = 0

        self.g = graph

        self.jobs_todo = []
        self.jobs_done = []

        self.completion_times = []

        # History of structure locations
        self.move_history = []
