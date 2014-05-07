"""

"""

def plan_paths(bots, map, waypoints, structure):

    rod_count = len(structure.es)
    node_count = len(structure.vs)

    build_station = waypoints['build_station']
    rod_feeds = waypoints['rod_feeds']
    glue_wells = waypoints['glue_wells']
    rotation_stations = waypoints['rotation_stations']
    indexing_stations = waypoints['indexing_stations']

    print('----- Planning Paths -----')
    print('GOAL: Build a truss with {} rods and {} nodes.'.format(rod_count, node_count))

    for bot in bots:
        bot.add_goal(rod_feeds[0])
        bot.add_goal(glue_wells[0])
        bot.add_goal(build_station)

    # At the end, bring all bots back to their initial positions
    for bot in bots:
        bot.add_goal(bot.pos)
    