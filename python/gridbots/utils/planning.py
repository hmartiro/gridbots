"""

"""

import logging

from gridbots.core.job import Job, Operation, Station
from gridbots.utils.graph import find_shortest_path

LINEAR_SPEED = 1.0


def plan_paths(graph, bots, stations, jobs):

    logging.info('------ TASK PLANNING ------')

    for job in jobs[:]:

        # Get the current operation
        op = job.current_op()
        #print('{} on {}'.format(job, op))

        # Check to see if the bot is finished
        if op.started:
            if job.bot and job.bot.at_goal():
                job.finish_op()

        # If the op is in progress, move on
        if op.started and not op.finished:
            logging.debug('{} has bot {} working on {}'.format(
                          job,
                          job.bot.name,
                          op.name
                          ))
            continue

        # If the job is finished, move on
        if job.finished:
            jobs.remove(job)
            job.bot.job = None
            logging.debug('{} is completed, bot {} is free'.format(
                          job,
                          job.bot.name
                          ))
            continue

        # If the last op is done, move to the next one
        if op.finished:
            job.move_to_next_op()
            op = job.current_op()

        # If the job doesn't have a bot, find one
        if not job.bot:

            # Get all available bots of the right type
            available_bots = [b for b in bots if (b.type == job.bot_type) and (not b.job)]

            # If there are none
            if not available_bots:
                logging.debug("{} can't find any bots for {}".format(
                              job,
                              op.name
                              ))
                continue

            else:
                # Choose the first one
                job.bot = available_bots[0]
                job.bot.op = op

        distances = {}
        for station in stations[op.name]:

            path = find_shortest_path(graph, job.bot.pos, station.pos)

            if not path:
                logging.warn("No path to station for {} found!".format(op.name))
                continue

            distances[station] = len(path)
            #logging.debug('distance to station at {}: {}'.format(station.pos, distances[station]))

        # Find fastest station by adding travel time to wait time
        # at arrival
        fastest_time = float("inf")
        fastest_station = None
        for station, distance in distances.items():
            time = distance * LINEAR_SPEED
            if time < fastest_time:
                fastest_time = time
                fastest_station = station

        # Assign goal to robot, register op w/ station
        if fastest_station:
            logging.debug('Assigning bot {} to station at node {} for op {}'.format(
                job.bot.name,
                fastest_station.pos,
                fastest_station.type
            ))
            #job.bot.goal = fastest_station.pos
            job.bot.assign_goal(fastest_station.pos)
            job.bot.job = job
            op.started = True
        else:
            logging.error('No way to accomplish {} found!'.format(op))
            continue


def create_job_queue(structure, job_types):
    """
    Given a goal structure return a queue of jobs that
    will build the structure.

    """
    job_queue = []

    def coords_from_edge(e):
        """ Get the vertex coordinates of an edge.
        """
        src = structure.vs.find(name=e.source)['coords']
        dest = structure.vs.find(name=e.target)['coords']
        return src, dest

    # Create a list of the edges in the structure
    edges = list(structure.es)

    # Sort edges by min Z coordinate, ascending
    edges.sort(key=lambda x: min([v[2] for v in coords_from_edge(x)]))

    # Sort edges by max Z coordinate, ascending
    edges.sort(key=lambda x: max([v[2] for v in coords_from_edge(x)]))

    # Iterate through the edges
    for e in edges:

        #print(min(coords_from_edge(e)), max(coords_from_edge(e)))

        # Get the edge coordinates
        c_src, c_dest = coords_from_edge(e)
        print(c_src, c_dest)
        # Find the type of rod
        if c_src[0] == c_dest[0] and c_src[1] == c_dest[1]:
            job_name = 'rod_z'
        elif c_src[0] == c_dest[0] and c_src[2] == c_dest[2]:
            job_name = 'rod_y'
        elif c_src[1] == c_dest[1] and c_src[2] == c_dest[2]:
            job_name = 'rod_x'
        else:
            raise NotImplementedError('Can only handle lattice structures!')

        job_type = job_types[job_name]

        job = Job(
            operations=job_type['operations'],
            platform_z=0,
            bot_type=job_type['bot_type']
        )
        job_queue.append(job)

    for j in job_queue:
        logging.info(j.operations)

    return job_queue
