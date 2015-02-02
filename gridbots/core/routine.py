"""

"""

import os
import re
import logging
from pprint import pformat

logging.basicConfig(format='%(message)s', level=logging.DEBUG)

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

    def __init__(self, scripts, *args, **kwargs):
        self.scripts = scripts
        super(ParallelCommands, self).__init__(*args, **kwargs)

    def __repr__(self):
        return '\nP' + list.__repr__(self)


class SerialCommands(list):

    def __init__(self, script, *args, **kwargs):
        self.script = script
        super(SerialCommands, self).__init__(*args, **kwargs)

    def __repr__(self):
        return '\nS({})'.format(self.script) + list.__repr__(self)


class TrajectoryBuilder():

    SCRIPT_DIR = os.path.join(gridbots.path, 'sri-scripts')

    # Switch rate of the board
    DEFAULT_RATE = 120  # Hz

    def __init__(self, path, script_name):

        self.rate = self.DEFAULT_RATE

        self.script = []

        self.commands = self.process_script(script_name)
        logging.debug('Commands:\n%s\n', self.commands)

        self.moves = self.generate_trajectory(self.commands)
        # logging.debug('Zone moves:\n%s\n', pformat(self.moves))

    def generate_trajectory(self, command):

        if isinstance(command, Command):

            if command.name == 'zmove':
                zone, x, y = command.args
                return self.zmove_to_trajectory(zone, float(x), float(y))

            elif command.name == 'rate':
                rate, = command.args
                self.rate = float(rate)
                return [{'rate': self.rate, 'script': list(self.script)}]

            elif command.name == 'zonewait':
                zone, time = command.args
                time = float(time)
                frames = int(time * self.rate)
                return [{
                    'zonewaiting_Z{}'.format(zone): time,
                    'script': list(self.script)
                } for i in range(frames)]

            elif command.name == 'wait':
                time, = command.args
                time = float(time)
                frames = int(time * self.rate)
                return [{'waiting': time, 'script': list(self.script)} for i in range(frames)]

            elif command.name == 'uv':
                state, = command.args
                state = int(state)
                return [{'uv': state, 'script': list(self.script)}]

            elif command.name == 'feed':
                feed_type, = command.args
                return [{'feed': feed_type, 'script': list(self.script)}]

            elif command.name == 'stagerel':
                x, y, z = [float(v) for v in command.args]
                return [{'stagerel': [x, y, z], 'script': list(self.script)}]

            else:
                logging.warning('Unknown command %s', command)
                return [{command.name: command.args, 'script': list(self.script)}]

        elif isinstance(command, SerialCommands):

            # Create a trajectory for each sub-command
            self.script.append(command.script)
            trajectories = [self.generate_trajectory(c) for c in command]

            self.script.pop()

            # Concatenate all moves together in order
            #serial_trajectory = [move for trajectory in trajectories for move in trajectory]
            serial_trajectory = [move for trajectory in trajectories for move in trajectory]

            return serial_trajectory

        elif isinstance(command, ParallelCommands):

            # Create a trajectory for each sub-command
            self.script.append(command.scripts)
            trajectories = [self.generate_trajectory(c) for c in command]
            self.script.pop()

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

    def zmove_to_trajectory(self, zone, x, y):

        # 0.5 mm converts to one edge
        x = int(2 * x)
        y = int(2 * y)

        zone_name = 'Z{:02}'.format(int(zone))

        trajectory = []

        x_move = '+X' if x > 0 else '-X'
        for i in range(abs(x)):
            trajectory.append({zone_name: x_move, 'script': list(self.script)})

        y_move = '+Y' if y > 0 else '-Y'
        for i in range(abs(y)):
            trajectory.append({zone_name: y_move, 'script': list(self.script)})

        return trajectory

    def read_script(self, script_name):

        # Get path to the script file
        script_path = os.path.join(self.SCRIPT_DIR, script_name.lower())

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
            logging.error('Script not found: %s', script_name)
            raise

        commands = SerialCommands(script=script_name)
        for i, line in enumerate(lines):
            logging.debug('Script %s, Line %s: %s', script_name, i+1, line)
            command = self.process_script_line(line)
            commands.append(command)
        return commands

    def process_script_line(self, line):

        if line.startswith('<'):
            # Found another script
            if '.txt' not in line:
                line += '.txt'

            return self.process_script(line[1:])

        elif line.startswith('simscript'):
            return self.process_simscript_line(line)

        if '(' not in line:
            # Found script that was incorrectly not prefixed w/ <
            if '.txt' not in line:
                line += '.txt'
            return self.process_script(line)

        command, args = line.split('(')
        command = command.strip()
        args = args[:-1].split(',')
        args = [a.strip() for a in args]
        return Command(command, args)

    def process_simscript_line(self, line):

        try:
            # NOTE ingoring closing parentheses since a lot of the scripts
            # incorrectly are missing them
            args = re.search('simscript\s*\((.*)', line).group(1)
        except AttributeError:
            logging.error('Bad line: %s', line)
            raise

        # Extract arguments
        paren_depth = 0
        start_inx = 0
        lines = []
        for i, c in enumerate(args):

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

            # NOTE removing trailing parenthesis to handle bad simcript invocation
            last_line = args[start_inx:]
            if last_line.count('(') - last_line.count(')') == -1:
                last_line = last_line[:-1]

            lines.append(last_line)

        # Strip whitespace
        lines = [c.strip() for c in lines]

        logging.debug('Simscript contains: %s', lines)

        parallel = ParallelCommands(scripts=[])
        for line in lines:
            command = self.process_script_line(line)
            parallel.append(command)
            if isinstance(command, SerialCommands):
                parallel.scripts.append(command.script)
                command.script = ''
            #     parallel.extend(command)
            # elif isinstance(command, Command):
            #     parallel.append(command)
            # else:
            #     raise Exception('Unexpected command: {}'.format(command))

        logging.debug('Simscript commands: %s', parallel)

        s = SerialCommands(script='simscript')
        s.append(parallel)
        return s

if __name__ == '__main__':

    import sys
    import yaml

    if len(sys.argv) < 2:
        top_level_script = 'units1&2_tree_int.txt'
    else:
        top_level_script = sys.argv[1]

    builder = TrajectoryBuilder(top_level_script)

    print(yaml.dump(builder.moves))
