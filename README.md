gridbots
========

Gridbots is a simulation and path-planning platform for the microbot construction project being developed at SRI:

http://www.scientificamerican.com/article/sri-magnetic-microbot-construction/

### Goals
* Understand and optimize the process of constructing structures with microbots.
* Visualize the process real-time in 2D and 3D.
* Given a desired structure and grid, output the necessary microbots and control trajectories to build it.

### Definitions
*Gridbots* - The name of the simulation platform  
*Bot* - A single microbot consisting of a base, magnet, and end-effectors  
*Map* - The grid of wiring that defines the locations microbots can travel  

### Algorithms and Data Structures
The core of this problem is representing the space in which the bots can move, the goals that they need to collectively accomplish, and the path-planning and coordination required to achieve those goals. Efficiency is critical to exploring the scalability of the system.

Due to the unique nature of the actuation system, the map consists of a set of discrete coordinates that microbots can occupy and a set of transition paths between coordinates. Based on these parameters, it makes sense to not perform path-planning using XY coordinates, but instead represent the map as an undirected graph. Each coordinate is represented as a vertex of the graph, and each transition is given by an edge. The graph is currently unweighted (assuming all transitions take equal time), but it is simple to weight by XY distance.

The location of each microbot, resource, and goal can be represented with a vertex ID (along with orientation). Shortest-path planning is easy using Dijkstra's algorithm, and the resulting path is represented as a list of vertices. Obstacles can be represented by removing a vertex. All calculations happen on the graph, and XY coordinates are only used for rendering.

### Implementation
The platform is implemented in Python, with a focus on simplicity and modularity. We want to define specific components of functionality (initialization, planning, rendering) and maintain abstraction between them.

###### Bot
The Bot class represents a single microbot's components, graph location, and future goals. 

###### Simulation
The Simulation class constructs the graph and performs all calculations. It takes two arguments, an input file and a renderer.

###### Renderer
The renderer is responsible for producing the output for the simulation. There are three types currently planned:
* The text renderer will output only a trajectory or control scheme, with no visuals. This is useful when we want to control a physical system rather than simulate, and also for running very large scale simulations in which rendering could be a bottleneck.
* The 2D renderer outputs a real-time top-view visualization of the system in action. The PyGameDrawer achieves this using the PyGame python library for both timing and drawing. This is most useful for simulating and understanding the platform.
* The 3D renderer will produce a more compelling visual output of the system with meshes, textures, and lighting. The Blender Game Engine is the planned tool. This is most useful for producing impressive and realistic looking videos.

###### Input File

Simulations are run by creating a Simulation class with the desired renderer and specifying an input file. The input file defines the map, microbots, resources, and goals in a standard YAML format. A vertex is specified by an id and coordinates, an edge by two vertex ids, a bot by its starting vertex, orientation, etc. Representation of resources and desired structures is not defined yet.

```
---
name: test_map

vertices: 
    - [0, [0.0, 10.0]]
    - [1, [5.0, 10.0]]
    - [2, [10.0, 10.0]]
    - [3, [0.0, 0.0]]
    - [4, [5.0, 0.0]]
    - [5, [10.0, 0.0]]
    - [6, [15.0, 5.0]]

edges:
    - [0, 1]
    - [1, 2]
    - [0, 3]
    - [1, 4]
    - [2, 5]
    - [3, 4]
    - [4, 5]
    - [2, 6]
    - [5, 6]

bots:
    0:
        position: 0
        orientation: "N"
        goals: [6, 1, 4, 5, 1, 6 ,0]
```

### TODO List

- Multi-bot avoidance
- Permanent obstacle capability
- Tasks (get resources, place into structure)
- End effectors
  - input of 
  - rotation points
  - rendering
- Goal generation based on paths
- Blender!
- Allow for missing vertex IDs
