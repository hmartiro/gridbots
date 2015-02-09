"""

"""

import os
import sys
import logging
import datetime
import mathutils as mu

import gridbots
from gridbots.generators.structure.ply_to_graph import ply_to_graph
from gridbots.generators.structure.structure_from_ply import fill_hollow_box_mesh
from gridbots.controllers.single_routine import RoutineController

LATTICE_SPACING = 12  # mm


class LatticeController():

    def __init__(self, sim, options):

        self.logger = logging.getLogger(__name__)

        self.sim = sim
        self.structure = self.sim.structure
        self.finished = False

        self.dual_build = True
        if 'dual_build' in options:
            self.dual_build = options['dual_build']

        self.structure_name = options['structure']
        self.structure_file = os.path.join(gridbots.path, 'spec', 'structures', self.structure_name)

        # Read the ply
        hollow_edges, hollow_verts = ply_to_graph(self.structure_file)

        # Fill in the build
        self.vertices, self.edges = fill_hollow_box_mesh(hollow_edges, hollow_verts)

        self.rod_queue = self.edges

        # Keep track of which rods we generated commands for
        self.processed = []

        # Current rod in the top-level loop
        self.inx = 0

        self.stage_pos = mu.Vector([0, 0, 0])

        self.modes = {
            'uninit',  # uninit
            'tree',  # putting down first layer of trees
            'tlap',  # putting down trees
            'vert',  # putting down verticals
            'horz'   # putting down horizontals
        }

        self.mode = 'uninit'

        # Generate the build commands
        self.commands = []
        self.generate_commands()

        script_str = '\n'.join(self.commands)
        self.logger.info(script_str)

        script_dir = os.path.join(gridbots.path, 'sri-scripts')
        script_name = '_{}.txt'.format(self.sim.sim_name)
        script_path = os.path.join(script_dir, script_name)

        with open(script_path, 'w') as f:
            f.write(script_str)

        # Use a RoutineController to read and run the script
        self.routine_controller = RoutineController(self.sim, {
            'routine': script_name
        })

    def comment(self, s):
        self.commands.append('# {}'.format(s))

    def command(self, name, *args):
        self.commands.append('{}({})'.format(name, ', '.join(str(a) for a in args)))

    def script(self, s):
        self.commands.append('<{}'.format(s))

    def separator(self):
        self.commands.append('# -------------------------------------------------------')

    def newline(self):
        self.commands.append('')
    
    def stagerel(self, x=0, y=0, z=0):
        self.command('stagerel', x, y, z)

    def _header(self):

        self.separator()
        self.comment('Autogenerated build script for')
        self.comment('    {}'.format(self.structure_file))
        self.comment('')
        self.comment('Date: {}'.format(str(datetime.datetime.now())))
        self.separator()
        self.newline()

    def _start_to_tree(self, v1):

        v1_mm = mu.Vector(v1) * LATTICE_SPACING

        self.comment('TRANSITION: start -> tree')
        self.separator()
        self.script('units1&2_buffer_reverse')
        self.script('units1&2_tree_ready')
        self.script('units1&2_buffer_reverse')
        self.newline()
        # self.stagerel(12, 0, 0)
        self.stagerel(v1_mm.x, v1_mm.y, v1_mm.z)
        self.stagerel(-6, 0, 0)
        self.separator()
        self.newline()

    def _tree(self, inx, v1, v2):

        v1_mm = mu.Vector(v1) * LATTICE_SPACING
        move = self.stage_pos - v1_mm
        self.stage_pos -= move

        if self.dual_build:
            parallel_inx = None
            i = inx + 1
            while i < len(self.rod_queue):
                u1, u2 = self.get_rod(i)
                if not self.is_x_rod(u1, u2):
                    break
                if u1[0] == v1[0] and u1[2] == v1[2] and abs(v1[1] - u1[1] - 2) < 1e-4:
                    parallel_inx = i
                    break
                i += 1

            if parallel_inx and not self.processed[parallel_inx]:
                u1, u2 = self.get_rod(i)
                self.comment('Place in parallel:')
                self.comment('Tree rod from {} to {}'.format(v1, v2))
                self.comment('Tree rod from {} to {}'.format(u1, u2))
                self.stagerel(move.x, move.y, move.z)
                self.script('units1&2_tree_int')
                self.stagerel(0, -12, 0)
                self.newline()

                self.processed[parallel_inx] = True
                self.processed[inx] = True
                return

        self.comment('Place tree rod from {} to {}'.format(v1, v2))
        self.stagerel(move.x, move.y, move.z)
        self.script('unit2_tree_int_AH.txt')
        self.newline()

    def _tree_to_vert(self):

        self.stagerel(6, 0, 0)
        self.newline()
        self.comment('TRANSITION: tree -> vert')
        self.separator()
        self.stagerel(0, 0, -12)
        self.script('units1&2_buffer_advance')
        self.script('units1&2_buffer_advance')
        self.newline()
        self.comment('Fix the glue gap')
        self.stagerel(1, -1, 0)
        self.newline()
        self.stagerel(8, 0, 0)
        self.separator()
        self.newline()

    def _vert(self, inx, v1, v2):

        v1_mm = mu.Vector(v1) * LATTICE_SPACING
        move = self.stage_pos - v1_mm
        self.stage_pos -= move

        if self.dual_build:
            parallel_inx = None
            i = inx + 1
            while i < len(self.rod_queue):
                u1, u2 = self.get_rod(i)
                if not self.is_z_rod(u1, u2):
                    break
                if u1[0] == v1[0] and u1[2] == v1[2] and abs(v1[1] - u1[1] - 2) < 1e-4:
                    parallel_inx = i
                    break
                i += 1

            if parallel_inx and not self.processed[parallel_inx]:
                u1, u2 = self.get_rod(i)
                self.comment('Place in parallel:')
                self.comment('Vertical rod from {} to {}'.format(v1, v2))
                self.comment('Vertical rod from {} to {}'.format(u1, u2))
                self.stagerel(move.x, move.y, move.z)
                self.script('units1&2_vert_int')
                self.stagerel(0, -12, 0)
                self.newline()
                self.processed[parallel_inx] = True
                self.processed[inx] = True
                return

        self.comment('Place vertical rod from {} to {}'.format(v1, v2))
        self.stagerel(move.x, move.y, move.z)
        self.script('unit2_vert_int')
        self.stagerel(0, -12, 0)
        self.newline()
        self.processed[inx] = True

    def _vert_to_horz(self):

        self.comment('Undo fix the glue gap')
        self.stagerel(-1, 1, 0)
        self.newline()
        self.comment('TRANSITION: vert -> horz')
        self.separator()
        self.stagerel(0, -12, 12)
        self.script('units1&2_buffer_reverse')
        self.script('units1&2_horz_ready')
        self.script('units1&2_buffer_reverse')
        self.script('units1&2_buffer_reverse')
        self.newline()
        self.comment('This is for rod alignment asymmetry ?')
        self.stagerel(0, -2, 0)
        self.newline()
        self.separator()
        self.newline()

    def _horz(self, inx, v1, v2):

        v1_mm = mu.Vector(v1) * LATTICE_SPACING
        move = self.stage_pos - v1_mm
        self.stage_pos -= move

        if self.dual_build:
            parallel_inx = None
            i = inx + 1
            while i < len(self.rod_queue):
                u1, u2 = self.get_rod(i)
                if not self.is_y_rod(u1, u2):
                    break
                if u1[0] == v1[0] and u1[2] == v1[2] and abs(v1[1] - u1[1] - 2) < 1e-4:
                    parallel_inx = i
                    break
                i += 1

            if parallel_inx and not self.processed[parallel_inx]:
                u1, u2 = self.get_rod(i)
                self.comment('Place in parallel:')
                self.comment('Horizontal rod from {} to {}'.format(v1, v2))
                self.comment('Horizontal rod from {} to {}'.format(u1, u2))
                self.stagerel(move.x, move.y, move.z)
                self.script('units1&2_horz_int')
                self.stagerel(0, 0, -12)
                self.newline()

                self.processed[parallel_inx] = True
                self.processed[inx] = True
                return

        self.comment('Place horizontal rod from {} to {}'.format(v1, v2))
        self.stagerel(move.x, move.y, move.z)
        self.script('unit2_horz_int')
        self.stagerel(0, -12, 0)
        self.newline()

    def _horz_to_tlap(self):

        self.comment('Undo rod alignment asymmetry ?')
        self.stagerel(0, 2, 0)
        self.newline()
        self.comment('TRANSITION: horz -> tlap')
        self.separator()
        self.script('units1&2_buffer_advance')
        self.script('units1&2_buffer_advance')
        self.script('units1&2_tree_ready')
        self.script('units1&2_buffer_advance')
        self.stagerel(-12, 12, 0)
        self.newline()
        self.separator()
        self.newline()

    def _tlap(self, inx, v1, v2):

        v1_mm = mu.Vector(v1) * LATTICE_SPACING
        move = self.stage_pos - v1_mm
        self.stage_pos -= move

        if self.dual_build:
            parallel_inx = None
            i = inx + 1
            while i < len(self.rod_queue):
                u1, u2 = self.get_rod(i)
                if not self.is_x_rod(u1, u2):
                    break
                if u1[0] == v1[0] and u1[2] == v1[2] and abs(v1[1] - u1[1] - 2) < 1e-4:
                    parallel_inx = i
                    break
                i += 1

            if parallel_inx and not self.processed[parallel_inx]:
                u1, u2 = self.get_rod(i)
                self.comment('Place in parallel:')
                self.comment('Tree rod from {} to {}'.format(v1, v2))
                self.comment('Tree rod from {} to {}'.format(u1, u2))
                self.stagerel(move.x, move.y, move.z)
                self.script('units1&2_tlap_int')
                self.stagerel(0, -12, 0)
                self.newline()

                self.processed[parallel_inx] = True
                self.processed[inx] = True
                return

        self.comment('Place tree rod from {} to {}'.format(v1, v2))
        self.stagerel(move.x, move.y, move.z)
        self.script('unit2_tlap_int')
        self.stagerel(0, -12, 0)
        self.newline()

    def _tlap_to_vert(self):

        self.comment('TRANSITION: tlap -> vert')
        self.separator()
        self.stagerel(12, 0, -12)
        self.newline()
        self.comment('align, getsolv, getwater_soak left out here')
        self.newline()
        self.comment('Fix the glue gap')
        self.stagerel(1, -1, 0)
        self.separator()
        self.newline()

    def _footer(self):

        self.separator()
        self.comment('End autogenerated build script')
        self.separator()
        self.newline()

    def handle_rod(self, inx):

        # Already built in a parallel step
        if self.processed[inx]:
            return

        rod = self.get_rod(inx)
        v1, v2 = rod

        # Tree rod is next
        if self.is_x_rod(v1, v2):

            if self.mode == 'tree':
                self._tree(inx, v1, v2)

            elif self.mode == 'horz':
                self._horz_to_tlap()
                self._tlap(inx, v1, v2)

            elif self.mode == 'tlap':
                self._tlap(inx, v1, v2)

            else:
                raise Exception('Cannot enter tlap mode from {}!'.format(self.mode))

            self.logger.info('tree rod: {}'.format(rod))

            if self.mode != 'tree':
                self.mode = 'tlap'

        # Horizontal rod is next
        elif self.is_y_rod(v1, v2):

            if self.mode == 'vert':
                self._vert_to_horz()
                self._horz(inx, v1, v2)

            elif self.mode == 'horz':
                self._horz(inx, v1, v2)

            else:
                raise Exception('Cannot enter horz mode from {}!'.format(self.mode))

            self.logger.info('horizontal rod: {}'.format(rod))
            self.mode = 'horz'

        # Vertical rod is next
        elif self.is_z_rod(v1, v2):

            if self.mode == 'tree':
                self._tree_to_vert()
                self._vert(inx, v1, v2)

            elif self.mode == 'tlap':
                self._tlap_to_vert()
                self._vert(inx, v1, v2)

            elif self.mode == 'vert':
                self._vert(inx, v1, v2)

            else:
                raise Exception('Cannot enter vert mode from {}!'.format(self.mode))

            self.logger.info('vertical rod: {}'.format(rod))
            self.mode = 'vert'

        else:
            raise Exception('Cannot tell type of active rod: {}'.format(rod))

    def get_rod(self, i):
        e = self.rod_queue[i]
        v1 = self.vertices[e[0]]
        v2 = self.vertices[e[1]]
        return v1, v2

    def generate_commands(self):

        self._header()

        self.mode = 'tree'

        # Create a set of tree attachment points by looking at the verticals
        # of the first layer
        tree_verts = set()
        for e in self.rod_queue:
            v1 = tuple(self.vertices[e[0]])
            v2 = tuple(self.vertices[e[1]])

            if not self.is_z_rod(v1, v2):
                break

            tree_verts.add(v1)
            tree_verts.add(v2)

        # Sort into build order
        tree_verts = list(tree_verts)
        tree_verts.sort(key=lambda p: (-p[0], -p[2], -p[1]))

        # Build the trees
        self._start_to_tree(tree_verts[0])

        # Prepend the tree rods
        tree_edges = []
        for i, v1 in enumerate(tree_verts):
            v2 = [v1[0]+1, v1[1], v1[2]]
            id1 = 'tree_{}_1'.format(i)
            id2 = 'tree_{}_2'.format(i)
            self.vertices[id1] = v1
            self.vertices[id2] = v2
            e = (id1, id2)
            tree_edges.append(e)

        self.rod_queue[:0] = tree_edges

        self.processed = [False] * len(self.rod_queue)

        while self.inx < len(self.rod_queue):

            self.handle_rod(self.inx)
            self.inx += 1

        self._footer()

    @staticmethod
    def is_x_rod(v1, v2):
        return (v1[1] - v2[1] == 0) and (v1[2] - v2[2] == 0)

    @staticmethod
    def is_z_rod(v1, v2):
        return (v1[0] - v2[0] == 0) and (v1[1] - v2[1] == 0)

    @staticmethod
    def is_y_rod(v1, v2):
        return (v1[0] - v2[0] == 0) and (v1[2] - v2[2] == 0)

    def step(self, frame):

        if frame >= len(self.routine_controller.routine):
            self.finished = True
            return {}

        return self.routine_controller.step(frame)
