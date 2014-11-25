"""

"""

import os
import re
import logging
from pprint import pprint, pformat

import gridbots


class Command():

    def __init__(self, name, args):
        self.name = name
        self.args = args

    def __repr__(self):
        return '{}({})'.format(
            self.name,
            ', '.join(self.args)
        )


class ParallelCommands(list):

    def __repr__(self):
        return 'P' + list.__repr__(self)


class SerialCommands(list):

    def __repr__(self):
        return 'S' + list.__repr__(self)


class TrajectoryBuilder():

    SCRIPT_DIR = os.path.join(gridbots.path, 'sri-scripts')

    def __init__(self, script_name):

        commands = self.process_script(script_name)
        logging.info('Commands:\n{}\n'.format(commands))

        zone_moves = self.generate_trajectory(commands)
        logging.info('Zone moves:\n{}\n'.format(pformat(zone_moves)))

    def generate_parallel_trajectory(self, commands):

        trajectories = []
        for command in commands:

            if type(command) == list:
                trajectories.append(self.generate_trajectory(command))

            else:
                name, args = command
                if name == 'zmove':
                    zone, x, y = args

                    # TODO handle non-integer movements
                    x = int(float(x))
                    y = int(float(y))
                    trajectories.append(self.zmove_to_trajectory(zone, x, y))

        merged = []
        for trajectory in trajectories:
            for i in range(len(trajectory)):
                try:
                    merged[i].update(trajectory[i])
                except IndexError:
                    merged.append(trajectory[i])

        logging.debug('output of generate_sim_trajectory: {}'.format(merged))
        return merged

    def generate_trajectory(self, command):

        if isinstance(command, Command):

            if command.name == 'zmove':

                zone, x, y = command.args

                # TODO handle non-integer movements
                x = int(float(x))
                y = int(float(y))
                return self.zmove_to_trajectory(zone, x, y)

            else:
                logging.warning('Skipping command {}'.format(command))
                return []

        elif isinstance(command, SerialCommands):

            # Create a trajectory for each sub-command
            trajectories = [self.generate_trajectory(c) for c in command]
            print(trajectories)
            # Concatenate all moves together in order
            serial_trajectory = [move for trajectory in trajectories for move in trajectory]
            return serial_trajectory

        elif isinstance(command, ParallelCommands):

            # Create a trajectory for each sub-command
            trajectories = [self.generate_trajectory(c) for c in command]

            # Merge moves from each sub-command together
            parallel_trajectory = []
            for trajectory in trajectories:
                for i in range(len(trajectory)):
                    try:
                        parallel_trajectory[i].update(trajectory[i])
                    except IndexError:
                        parallel_trajectory.append(trajectory[i])
            return parallel_trajectory

        else:
            raise RuntimeError('Unknown command of type {}: {}'.format(
                type(command), command
            ))

    @staticmethod
    def zmove_to_trajectory(zone, x, y):

        trajectory = []

        x_move = '+X' if x > 0 else '-X'
        for i in range(abs(x)):
            trajectory.append({zone: x_move})

        y_move = '+Y' if y > 0 else '-Y'
        for i in range(abs(y)):
            trajectory.append({zone: y_move})

        return trajectory

    def read_script(self, script_name):

        # Get path to the script file
        script_path = os.path.join(self.SCRIPT_DIR, '{}.txt'.format(script_name))

        # Read the script as a list of lines
        with open(script_path, 'r') as f:
            lines = f.readlines()

        # Strip any whitespace
        lines = [l.strip() for l in lines]

        # Filter out blank lines
        lines = [l for l in lines if l != '']

        # Filter out comments
        lines = [l for l in lines if l[0] != '#' and l[1] != '#']

        return lines

    def process_script(self, script_name):

        try:
            lines = self.read_script(script_name)
        except FileNotFoundError:
            logging.error('Script not found: {}'.format(script_name))
            return [('SCRIPT NOT FOUND: {}'.format(script_name), [])]

        commands = SerialCommands()
        for i, line in enumerate(lines):
            logging.debug('Script {}, Line {}: {}'.format(script_name, i+1, line))
            command = self.process_script_line(line)
            if isinstance(command, Command):
                commands.append(command)
            else:
                commands.extend(command)
        return commands

    def process_script_line(self, line):

        if line.startswith('<'):
            return self.process_script(line[1:])

        elif line.startswith('simscript'):
            return self.process_simscript_line(line)

        if '(' not in line:
            return self.process_script(line)

        command, args = line.split('(')
        args = args[:-1].split(',')
        args = [a.strip() for a in args]
        return Command(command, args)

    def process_simscript_line(self, line):

        try:
            args = re.search('simscript\s*\((.*)\)', line).group(1)
        except AttributeError:
            logging.error('Bad line: {}'.format(line))
            raise

        # Extract arguments
        paren_depth = 0
        start_inx = 0
        lines = []
        for i, c in enumerate(args):

            # logging.debug('i: {}, c: {}, paren: {}, start_inx: {}, str: {}'.format(
            #     i, c, paren_depth, start_inx, args[start_inx:i])
            # )

            if c == '(':
                paren_depth += 1
                continue

            elif c == ')':
                paren_depth -= 1

            elif c == ',':
                if paren_depth == 0:
                    lines.append(args[start_inx:i])
                    start_inx = i+1

        if start_inx < len(args):
            lines.append(args[start_inx:])

        # Strip whitespace
        lines = [c.strip() for c in lines]

        logging.debug('Simscript contains: {}'.format(lines))

        commands = ParallelCommands()
        for line in lines:
            commands.append(self.process_script_line(line))

        logging.debug('Simscript commands: {}'.format(commands))
        return [commands]

if __name__ == '__main__':

    import sys
    import yaml

    if len(sys.argv) < 2:
        top_level_script = 'units1&2_tree_int'
    else:
        top_level_script = sys.argv[1]

    s = TrajectoryBuilder(top_level_script)
