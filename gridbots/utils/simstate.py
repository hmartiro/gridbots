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
        self.time = None

    def set_bots(self, bots):
        self.bots = {b.name: (tuple(b.pos/24), b.rot) for b_name, b in bots.items()}

    def set_structure(self, structure):
        self.structure = tuple(structure.pos/24)
        self.rods = {rod_id: (
            rod['bot'],
            tuple(rod['pos']/24) if rod['pos'] is not None else None,
            rod['rot'],
            rod['done']
        ) for rod_id, rod in structure.rods.items()}

    def set_scripts(self, scripts, time):
        self.scripts = scripts
        self.time = time

    def serialize(self):
        return pickle.dumps((
            self.frame,
            self.bots,
            self.rods,
            self.structure,
            self.scripts,
            self.time
        ))

    @classmethod
    def deserialize(cls, serialized_state):
        data = pickle.loads(serialized_state)
        s = SimulationState(data[0])
        s.bots = data[1]
        s.rods = data[2]
        s.structure = data[3]
        s.scripts = data[4]
        s.time = data[5]
        return s
