gridbots
========

Gridbots is a simulation and path-planning platform for the microbot construction project being developed at SRI International. They are pioneering a system of ant-sized robots that move at incredible speeds, swarm over surfaces, and use tools to construct macro-scale structures. This unique technology has potential to improve the manufacturing of everything from small biomedical devices to airplane wings.

* [New York Times](http://bits.blogs.nytimes.com/2014/04/19/a-swarm-of-tiny-ant-sized-robots-at-your-service/?_php=true&_type=blogs&_r=0)
* [Engadget](http://www.engadget.com/2014/04/17/sri-microbots/)
* [Wired](http://www.wired.co.uk/news/archive/2014-04/16/magnetic-microrobot-swarms)
* [Scientific American](http://www.scientificamerican.com/article/sri-magnetic-microbot-construction/)
* [IEEE Spectrum](http://spectrum.ieee.org/automaton/robotics/industrial-robots/watch-sris-nimble-microrobots-cooperate-to-build-structures)

The Gridbots project aims to build a set of algorithms that coordinate thousands of micro robots towards a unified goal. It tackles the problems of path-planning, obstacle avoidance, data modeling, task allocation, and makespan optimization.

### Goals
* Understand and optimize the process of constructing structures with microbots.
* Visualize the process real-time in 2D and 3D.
* Given available tools and goal structure, generate the output trajectories to build it.

### Definitions
*Gridbots* - The name of this simulation platform 
*Bot* - A single microbot consisting of a base, magnets, and end-effectors  
*Node* - A single location in space that a bot can occupy
*Edge* - A pathway that a bot can traverse between Nodes
*Map* - Navigable space of the bots, defined by a set of Nodes and Edges between them
*Structure* - The desired output structure (ex: a carbon fiber truss)
*Job* - The procedure of building a single component of the final structure
*Operation* - A single concrete step out of multiple that make up a Job (ex: applying glue)
*Station* - A Node at which an Operation can be completed (ex: a glue station)
*Simulation* - A specification of a Map, Bots, Stations, and Structure that define a simulation scenario
*Path* - Output of a Simulation, a set of trajectories for each bot that build the Structure
*Renderer* - An entity that takes the Paths for a certain Simulation and visualizes the data

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

* UPDATE *
Simulations are run by creating a Simulation class with the desired renderer and specifying an input file. The input file defines the map, microbots, resources, and goals in a standard YAML format. A vertex is specified by an id and coordinates, an edge by two vertex ids, a bot by its starting vertex, orientation, etc. Representation of resources and desired structures is not defined yet.


### Structure planning

Truss structure is defined as a graph in 3D
- assume XZ plane for now
- assume cubic lattice only for now

- Sort edges by minimum z value, with the lowest first
- Sort again by maximum z value, with the lowest first
- Take next edge
  - set platform location to min Z value
  - create job w/ rod info and XZ info
    - rod orientation
    - rod length
    - glue requirements
    - X position
    - Z position
