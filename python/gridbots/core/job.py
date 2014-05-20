"""

"""


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

    def __init__(self, operations, platform_z):

        self.operations = []
        for op_name in operations:
            op = Operation(op_name)
            self.operations.append(op)

        if self.operations:
            self.finished = False
            self.current_op_inx = 0
        else:
            self.finished = True

        # Platform position for dropoff
        self.platform_z = platform_z

        # Robot currently assigned to the job
        self.bot = None

    def current_op(self):

        if self.finished:
            return None

        return self.operations[self.current_op_inx]

    def finish_op(self):
        """ Finish the current operation and move on.
        """
        self.current_op().finished = True
        self.current_op_inx += 1

        if all([op.finished for op in self.operations]):
            self.finished = True

    def start_op(self):
        """ Start progress on the current operation.
        """
        self.current_op().started = True

    def __repr__(self):
        """ String representation
        """
        return '<Job> Operations: {}/{}'.format(
            self.current_op_inx,
            len(self.operations)
        )
