"""

"""

import logging

from gridbots.core.job import Job
from gridbots.core.job import Operation

def plan_paths(bots, map, structure, simulation_data):

    rod_count = len(structure.es)
    node_count = len(structure.vs)

    waypoints = simulation_data['waypoints']
    build_order = simulation_data['build_order']

    print(build_order)

    logging.info('----- Planning Paths -----')
    logging.info('GOAL: Build a truss with {} rods and {} nodes.'.format(rod_count, node_count))

    jobs_data = simulation_data['jobs']

    jobs = []
    for job_data in jobs_data:
        job = Job(job_data, 0)
        jobs.append(job)

    for job in jobs:
        op = job.current_op()
        print('{} on {}'.format(job, op))

        if op.started and not op.finished:
            continue

        if job.finished:
            jobs.remove(job)
            continue

        if not job.bot:

            # Get all available bots
            available_bots = [bot for bot in bots if not bot.job]

            if not available_bots:
                continue

            else:
                # Choose the first one
                job.bot = available_bots[0]
                job.bot.job = job

        print job.bot
        job.bot.goal = 5

    # for bot in bots:
    #     for build_step in build_order:
    #         waypoint = waypoints[build_step][0]
    #         #bot.add_goal(waypoint['position'])

    # At the end, bring all bots back to their initial positions
    #for bot in bots:
    #    bot.add_goal(bot.pos)
