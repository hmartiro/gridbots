"""

"""


class Station:

    def __init__(self, station_type, position, time):

        self.type = station_type
        self.pos = position

        self.time = time

        # How long until this station is available
        self.wait_time = 0

    def __repr__(self):

        return '<Station> type {} at {}'.format(
            self.type,
            self.pos
        )


class Operation:

    def __init__(self, name):

        self.name = name

        self.started = False
        self.finished = False

    def __repr__(self):
        """ String representation
        """
        return '<Op> {}, Started: {}, Finished: {}'.format(self.name, self.started, self.finished)


class Job:

    def __init__(self, operations, bot_type, edge):

        self.operations = []
        for op_name in operations:
            op = Operation(op_name)
            self.operations.append(op)

        if self.operations:
            self.finished = False
            self.current_op_inx = 0
        else:
            self.finished = True

        self.bot_type = bot_type

        # Which truss am I building?
        self.edge = edge

        # Robot currently assigned to the job
        self.bot = None

    def current_op(self):

        if self.finished:
            return None

        return self.operations[self.current_op_inx]

    def finish_op(self):
        """ Finish the current operation.
        """
        self.current_op().finished = True

        if all([op.finished for op in self.operations]):
            self.finished = True

    def move_to_next_op(self):

        self.current_op_inx += 1

    def start_op(self):
        """ Move on to the next operation.
        """

        self.current_op().started = True

    def __repr__(self):
        """ String representation
        """
        return '<Job> Operations: {}/{}'.format(
            self.current_op_inx,
            len(self.operations)
        )
