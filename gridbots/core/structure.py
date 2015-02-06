"""

"""

import logging
from gridbots.utils.maputils import pos_from_node
from gridbots.generators.structure.ply_to_graph import ply_to_graph
from gridbots.generators.structure.structure_from_ply import fill_hollow_box_mesh

import mathutils as mu
import math


class Structure:

    # If a rod on a bot is past this line and the uv comes on,
    # detach it - now belongs to the stage
    ROD_DETACH_MIN_X = 278  # mm

    ROD_PICKUP_MAX_X = -126  # mm
    ROD_PICKUP_MIN_Y = 120  # mm

    def __init__(self, sim, structure_file):

        self.logger = logging.getLogger(__name__)

        self.sim = sim
        self.structure_file = structure_file

        # Read the ply
        hollow_edges, hollow_verts = ply_to_graph(structure_file)

        # Fill in the build
        self.vertices, self.edges = fill_hollow_box_mesh(hollow_edges, hollow_verts)

        self.pos = mu.Vector(self.sim.sim_data['stage_pos'])

        # Rods
        self.rods = {}
        self.rod_id = 1

        self.rod_type_to_feed_node = {
            'h': self.sim.node_aliases['rod_feed_tree'],
            'v': self.sim.node_aliases['rod_feed_tree']  # TODO this is wrong
        }

        # Rods (by id) that are waiting to be picked up
        self.pending_rods = set()

        # TODO duplicated from blender.py
        self.bot_to_rod_pos_offset = {
            'bot_rod_h': mu.Vector([.47136, 0, .17335]),
            'bot_rod_v': mu.Vector([.47136, 0, .30]),
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
            stage_move = mu.Vector(control_inputs['stagerel'])
            self.pos += stage_move
            self.logger.info('Moving stage by %s, new pos %s', stage_move, self.pos)

        # Process new rods
        if 'feed' in control_inputs:
            rod_type = control_inputs['feed']
            feed_node = self.rod_type_to_feed_node[rod_type]

            rot = mu.Matrix.Rotation(math.radians(180.0), 4, 'Z')

            feed_pos = pos_from_node(self.sim.map, feed_node)

            # TODO determine from which type of robot will pick up
            bot_to_rod_offset = self.bot_to_rod_pos_offset['bot_rod_h'] * 24
            rod_pos = feed_pos + rot * bot_to_rod_offset
            rod_rot = 0, 0, 0

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

                        # if bot.type != 'bot_rod_v' and bot.type != 'bot_rod_h':
                        #     continue

                        if bot.pos.x > self.ROD_DETACH_MIN_X:

                            rot = mu.Matrix.Rotation(bot.rot, 4, 'Z')
                            bot_to_rod_offset = self.bot_to_rod_pos_offset[bot.type] * 24
                            print('Type: {}, Offset: {}'.format(rod_data['type'], bot_to_rod_offset))

                            rod_pos = bot.pos + rot * bot_to_rod_offset
                            rod_pos -= self.pos

                            if bot.type == 'bot_rod_h':
                                rod_rot = 0, 0, bot.rot
                            elif bot.type == 'bot_rod_v':
                                rod_rot = math.radians(90), 0, bot.rot
                            else:
                                raise Exception('Unknown bot type: {}'.format(bot.type))

                            rod_data['bot'] = None
                            rod_data['pos'] = rod_pos
                            rod_data['rot'] = rod_rot
                            rod_data['done'] = True
                            self.logger.info(
                                'Rod {} detached at frame {}, stage at {}, rod at {}, rod rotation {}'.format(
                                    rod_id, self.sim.frame, self.pos, (rod_pos + self.pos)/24, rod_rot
                                ))
            else:
                self.logger.info('UV turned off on frame {}'.format(self.sim.frame))

        # If pending rods, look for a bot nearby that picks it up
        if self.pending_rods:
            for bot in self.sim.bots:
                for rod_id in set(self.pending_rods):
                    if (bot.pos.x < self.ROD_PICKUP_MAX_X) and (bot.pos.y > self.ROD_PICKUP_MIN_Y):
                        self.pending_rods.remove(rod_id)
                        self.rods[rod_id]['bot'] = bot.name
                        self.rods[rod_id]['pos'] = None
                        self.rods[rod_id]['rot'] = None

                        self.logger.info('Bot {} ({}) at {} picked up rod {} at {} on frame {}'.format(
                            bot.name, bot.type, bot.pos, rod_id, self.rods[rod_id]['pos'], self.sim.frame
                        ))
                        self.logger.info('Scripts: {}'.format(self.sim.last_control_input))
