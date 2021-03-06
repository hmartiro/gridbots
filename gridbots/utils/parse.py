"""

"""

import os
import yaml
import gridbots


def parse_jobs(jobs_data, job_types):

    from gridbots.core.job import Job

    job_queue = []
    for j_data in jobs_data:

        job_type = job_types[j_data['type']]

        job = Job(
            operations=job_type['operations'],
            bot_type=job_type['bot_type'],
            edge=None  # TODO
        )
        job_queue.append(job)

    return job_queue


def parse_bots(bots_data, node_aliases, graph):

    from gridbots.core.bot import Bot

    bots = []
    for bot_name, bot_data in bots_data.items():

        if bot_data['position'] in node_aliases:
            bot_data['position'] = node_aliases[bot_data['position']]

        bot = Bot(
            name=bot_name,
            node=bot_data['position'],
            rotation=bot_data['rotation'],
            bot_type=bot_data['type'],
            graph=graph
        )
        bots.append(bot)

    return bots


def parse_stations(station_data, node_aliases):

    from gridbots.core.job import Station

    stations = {}
    for station_type in station_data.keys():

        stations[station_type] = []
        for s_data in station_data[station_type]:

            if s_data['position'] in node_aliases:
                s_data['position'] = node_aliases[s_data['position']]

            s = Station(
                station_type=station_type,
                position=s_data['position'],
                time=s_data['time']
            )
            stations[station_type].append(s)

    return stations


def parse_routine(routine):

    from gridbots.core.routine import TrajectoryBuilder

    path = os.path.join(gridbots.path, 'sri-scripts')
    builder = TrajectoryBuilder(path, routine)
    return builder.moves
