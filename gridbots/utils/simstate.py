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

    def set_bots(self, bots, prev=None):

        # self.bots = {b.name: (tuple(b.pos/24), b.rot) for b_name, b in bots.items()}
        for bot_name, bot in bots.items():
            data = (tuple(bot.pos/24), bot.rot)
            if not prev or data != prev.bots[bot_name]:
                self.bots[bot_name] = data

    def set_structure(self, structure, prev=None):

        # self.structure = tuple(structure.pos/24)
        structure_data = tuple(structure.pos/24)
        if not prev or structure_data != prev.structure:
            self.structure = structure_data

        for rod_id, rod in structure.rods.items():
            rod_data = (
                rod['bot'],
                tuple(rod['pos']/24) if rod['pos'] is not None else None,
                rod['rot'],
                rod['done']
            )
            if not prev or rod_id not in prev.rods or rod_data != prev.rods[rod_id]:
                self.rods[rod_id] = rod_data

        # self.rods = {rod_id: (
        #     rod['bot'],
        #     tuple(rod['pos']/24) if rod['pos'] is not None else None,
        #     rod['rot'],
        #     rod['done']
        # ) for rod_id, rod in structure.rods.items()}

    def set_scripts(self, scripts, time, prev=None):

        if not prev or scripts != prev.scripts:
            self.scripts = scripts

        if not prev or time != prev.time:
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
