"""

"""

def plan_paths(bots, map, structure, simulation_data):

    rod_count = len(structure.es)
    node_count = len(structure.vs)

    waypoints = simulation_data['waypoints']
    build_order = simulation_data['build_order']

    print(build_order)

    print('----- Planning Paths -----')
    print('GOAL: Build a truss with {} rods and {} nodes.'.format(rod_count, node_count))

    for bot in bots:
        for build_step in build_order:
            waypoint = waypoints[build_step][0]
            #bot.add_goal(waypoint['position'])

    # At the end, bring all bots back to their initial positions
    #for bot in bots:
    #    bot.add_goal(bot.pos)
    