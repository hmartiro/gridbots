"""

"""

import pickle


class SimulationState():

    def __init__(self, frame):

        self.frame = frame
        self.bots = {}
        self.rods = {}
        self.structure = None
        self.scripts = []

    def set_bots(self, bots):
        for bot in bots:
            self.bots[bot.name] = (tuple(bot.pos/24), bot.rot)

    def set_structure(self, structure):
        self.structure = tuple(structure.pos/24)
        for rod_id, rod in structure.rods.items():
            self.rods[rod_id] = (
                rod['type'],
                rod['bot'],
                tuple(rod['pos']/24) if rod['pos'] is not None else None,
                rod['rot'],
                rod['done']
            )

    def set_scripts(self, scripts):
        self.scripts = scripts

    def serialize(self):
        return pickle.dumps((
            self.frame,
            self.bots,
            self.rods,
            self.structure,
            self.scripts
        ))

    @classmethod
    def deserialize(cls, serialized_state):
        data = pickle.loads(serialized_state)
        s = SimulationState(data[0])
        s.bots = data[1]
        s.rods = data[2]
        s.structure = data[3]
        s.scripts = data[4]
        return s
