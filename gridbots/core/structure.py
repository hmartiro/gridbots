"""

"""

import logging
from gridbots.core.bot import Bot
from gridbots.utils.maputils import pos_from_node, node_from_pos
from copy import deepcopy


class Structure:

    def __init__(self, sim, graph):

        self.logger = logging.getLogger(__name__)

        self.pos = [0, 0, 0]

        self.sim = sim
        self.g = graph

        # History of stage locations
        self.move_history = [self.pos]

        # Rods
        self.rods = {}
        self.rod_history = [{}]
        self.rod_id = 1

        self.rod_type_to_feed_node = {
            'h': self.sim.node_aliases['rod_feed_tree'],
            'v': self.sim.node_aliases['rod_feed_tree']  # TODO this is wrong
        }

        # Rods (by id) that are waiting to be picked up
        self.pending_rods = set()

    def new_rod(self, rod_type, pos):
        """
        Create a new rod with a unique ID. Specify a type and an initial position.
        """
        rod_id = self.rod_id
        self.rod_id += 1

        self.rods[rod_id] = {
            'type': rod_type,
            'bot': None,
            'pos': pos
        }

        return rod_id

    def update(self, control_inputs):

        # Process stage movements
        if 'stagerel' in control_inputs:
            stage_move = control_inputs['stagerel']
            self.logger.info('Moving stage by %s', stage_move)
            self.pos = [v + stage_move[i] for i, v in enumerate(self.pos)]

        # Process new rods
        if 'feed' in control_inputs:
            rod_type = control_inputs['feed']
            feed_node = self.rod_type_to_feed_node[rod_type]
            pos = pos_from_node(self.sim.map, feed_node)
            new_rod_id = self.new_rod(rod_type, pos)
            self.pending_rods.add(new_rod_id)
            self.logger.info('New rod {} on frame {}'.format(new_rod_id, self.sim.frame))

        # If pending rods, look for a bot nearby that picks it up
        if self.pending_rods:
            for bot in self.sim.bots:
                for rod_id in set(self.pending_rods):
                    dist = bot.distance_to(self.rods[rod_id]['pos'])
                    if dist < 5:
                        self.pending_rods.remove(rod_id)
                        self.rods[rod_id]['bot'] = bot.name
                        self.rods[rod_id]['pos'] = None
                        self.logger.info('Bot {} picked up rod {} at {} on frame {}'.format(
                            bot.name, rod_id, self.rods[rod_id]['pos'], self.sim.frame
                        ))

        self.move_history.append(self.pos)
        self.rod_history.append(deepcopy(self.rods))
