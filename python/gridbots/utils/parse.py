"""

"""


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


def parse_bots(bots_data, sim):

    from gridbots.core.bot import Bot

    bots = []
    for bot_name, bot_data in bots_data.items():

        bot = Bot(
            name=bot_name,
            position=bot_data['position'],
            bot_type=bot_data['type'],
            sim=sim
        )
        bots.append(bot)

    return bots


def parse_stations(station_data):

    from gridbots.core.job import Station

    stations = {}
    for station_type in station_data.keys():

        stations[station_type] = []
        for s_data in station_data[station_type]:

            s = Station(
                station_type=station_type,
                position=s_data['position'],
                time=s_data['time']
            )
            stations[station_type].append(s)

    return stations
