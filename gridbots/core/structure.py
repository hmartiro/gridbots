"""

"""

import logging
from gridbots.core.bot import Bot
from gridbots.utils.maputils import pos_from_node, node_from_pos
from copy import deepcopy
import mathutils as mu
import math


class Structure:

    # If a rod on a bot is past this line and the uv comes on,
    # detach it - now belongs to the stage
    ROD_DETACH_MIN_X = 278  # mm

    ROD_PICKUP_MAX_X = -124  # mm
    ROD_PICKUP_MIN_Y = 120  # mm

    def __init__(self, sim, graph):

        self.logger = logging.getLogger(__name__)

        self.sim = sim
        self.g = graph

        self.pos = self.sim.sim_data['stage_pos']

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

        # TODO duplicated from blender.py
        self.bot_to_rod_pos_offset = {
            'h': mu.Vector([.47136*24, 0, .17335*24]),
            'v': mu.Vector([.47136*24, 0, .20895*24]),
        }

    def new_rod(self, rod_type, pos, rot):
        """
        Create a new rod with a unique ID. Specify a type and an initial position.
        """
        rod_id = self.rod_id
        self.rod_id += 1

        self.rods[rod_id] = {
            'type': rod_type,
            'bot': None,
            'pos': pos,
            'rot': rot,
            'done': False
        }

        return rod_id

    def update(self, control_inputs):

        # Process stage movements
        if 'stagerel' in control_inputs:
            stage_move = control_inputs['stagerel']
            self.pos = [v + stage_move[i] for i, v in enumerate(self.pos)]
            self.logger.info('Moving stage by %s, new pos %s', stage_move, self.pos)

        # Process new rods
        if 'feed' in control_inputs:
            rod_type = control_inputs['feed']
            feed_node = self.rod_type_to_feed_node[rod_type]

            rot = mu.Matrix.Rotation(math.radians(180.0), 4, 'Z')

            feed_pos = mu.Vector(pos_from_node(self.sim.map, feed_node))
            rod_pos = feed_pos + rot * self.bot_to_rod_pos_offset[rod_type]
            rod_pos = rod_pos.x, rod_pos.y, rod_pos.z

            rod_rot = 0, 0, 0
            self.logger.info('Feed pos: {}, offset: {}'.format(feed_pos, self.bot_to_rod_pos_offset[rod_type]))

            new_rod_id = self.new_rod(rod_type, rod_pos, rod_rot)
            self.pending_rods.add(new_rod_id)
            self.logger.info('New rod {} of type {} on frame {}'.format(new_rod_id, rod_type, self.sim.frame))

        if 'uv' in control_inputs:
            on = (control_inputs['uv'] == 1)
            if on:
                self.logger.info('UV turned on on frame {}'.format(self.sim.frame))
                for rod_id, rod_data in self.rods.items():
                    if rod_data['bot']:
                        bot = self.sim.bot_dict[rod_data['bot']]
                        pos = mu.Vector(pos_from_node(self.sim.map, bot.pos))

                        if pos[0] > self.ROD_DETACH_MIN_X:

                            rot = mu.Matrix.Rotation(self.sim.bot_dict[rod_data['bot']].rot, 4, 'Z')
                            rod_pos = pos + rot * self.bot_to_rod_pos_offset[rod_data['type']]
                            rod_pos -= mu.Vector(self.pos)
                            rod_pos = rod_pos.x, rod_pos.y, rod_pos.z

                            if bot.type == 'bot_rod_h':
                                rod_rot = 0, 0, self.sim.bot_dict[rod_data['bot']].rot
                            elif bot.type == 'bot_rod_v':
                                rod_rot = math.radians(90), 0, self.sim.bot_dict[rod_data['bot']].rot
                            else:
                                raise Exception('Unknown bot type: {}'.format(bot.type))

                            rod_data['bot'] = None
                            rod_data['pos'] = rod_pos
                            rod_data['rot'] = rod_rot
                            rod_data['done'] = True
                            self.logger.info(
                                'Rod detached at frame {}, stage at {}, offset {}, rod rotation {}'.format(
                                self.sim.frame, self.pos, rod_pos, rod_rot
                                ))
            else:
                self.logger.info('UV turned off on frame {}'.format(self.sim.frame))

        # If pending rods, look for a bot nearby that picks it up
        if self.pending_rods:
            for bot in self.sim.bots:
                bot_pos = pos_from_node(self.sim.map, bot.pos)
                for rod_id in set(self.pending_rods):
                    if (bot_pos[0] < self.ROD_PICKUP_MAX_X) and (bot_pos[1] > self.ROD_PICKUP_MIN_Y):
                        self.pending_rods.remove(rod_id)
                        self.rods[rod_id]['bot'] = bot.name
                        self.rods[rod_id]['pos'] = None
                        self.rods[rod_id]['rot'] = None

                        self.logger.info('Bot {} ({}) at {} picked up rod {} at {} on frame {}'.format(
                            bot.name, bot.type, bot_pos, rod_id, self.rods[rod_id]['pos'], self.sim.frame
                        ))

        self.move_history.append(self.pos)
        self.rod_history.append(deepcopy(self.rods))
