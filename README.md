gridbots
========

Gridbots is a simulation and path-planning platform for the microbot construction project being 
developed at SRI International. They are pioneering a system of ant-sized robots that move at 
incredible speeds, swarm over surfaces, and use tools to construct macro-scale structures. This 
unique technology has potential to improve the manufacturing of everything from small biomedical 
devices to airplane wings.

* [New York Times](http://bits.blogs.nytimes.com/2014/04/19/a-swarm-of-tiny-ant-sized-robots-at-your-service/?_php=true&_type=blogs&_r=0)
* [Engadget](http://www.engadget.com/2014/04/17/sri-microbots/)
* [Wired](http://www.wired.co.uk/news/archive/2014-04/16/magnetic-microrobot-swarms)
* [Scientific American](http://www.scientificamerican.com/article/sri-magnetic-microbot-construction/)
* [IEEE Spectrum](http://spectrum.ieee.org/automaton/robotics/industrial-robots/watch-sris-nimble-microrobots-cooperate-to-build-structures)

The Gridbots project aims to build a set of algorithms and strategies that coordinate thousands
of micro robots towards a unified goal. It tackles the problems of path-planning, obstacle
avoidance, data modeling, task allocation, and makespan optimization.

### Goals
* Understand and optimize the process of constructing structures with microbots.
* Visualize the process real-time in 2D and 3D.
* Given available tools and a goal structure, generate an instruction set to build it.

### Definitions
- *Gridbots* - The name of this simulation platform
- *Bot* - A single micro robot consisting of a base, magnets, and end-effectors
- *Node* - A single location in space that a bot can occupy
- *Edge* - A pathway that a bot can traverse between Nodes
- *Map* - Navigable space of the bots, defined by a set of Nodes and Edges between them
- *Structure* - The desired output structure (ex: a carbon fiber truss)
- *Job* - The procedure of building a single component of the final structure
- *Operation* - A single concrete step out of multiple that make up a Job (ex: applying glue)
- *Station* - A Node at which an Operation can be completed (ex: a glue station)
- *Simulation* - A specification of a Map, Bots, Stations, and Structure that define a simulation scenario
- *Path* - Output of a Simulation, a set of trajectories for each bot that build the Structure
- *Renderer* - An entity that takes the Paths for a certain Simulation and visualizes the process

### Algorithms and Data Structures
The core of this problem is representing the space in which the bots can move, the goals that they
need to collectively accomplish, and the path-planning and coordination required to achieve those
goals. Computational efficiency is critical to exploring the scalability of the system.

Due to the unique nature of the actuation system, the map consists of a set of discrete coordinates
that microbots can occupy and a set of transition paths between coordinates. Thus, it makes sense
not to approach path-planning using XY coordinates, but instead represent the map as a graph data
structure where bots occupy nodes and move along edges. The graph is currently unweighted (assuming
all transitions take equal time), and undirected (all paths are bidirectional), but it is easy to
weight by XY distance and use directed edges.

The location of each bot and meaningful point on the map can be represented with node IDs. Nodes 
are associated with XY coordinates. Shortest-path planning is easy using Dijkstra's algorithm, 
and the resulting path is represented as a list of vertices. Obstacles can be represented by 
removing a vertex. All calculations happen on the graph, and XY coordinates are only used for 
rendering.

### Installation guide
Tested on Ubuntu only, should work on most platforms with Python 3. You may need to modify
the pathfinding logic in `run.py` if there are import errors.

Clone the repository:

    git clone git@github.com:hmartiro/gridbots.git gridbots

Install Blender (used for 3D rendering):

    apt-get install blender

Install Python packages. Note, this may take a long time if numpy has to be compiled.

    cd gridbots
    pip3 install -r requirements.txt

Run:

    cd python/gridbots
    ./run.py [sim_name]

This will run the simulation in the given file and open a window to play back the results.

**Note:** I recommend adding `/path/to/gridbots/python` to your
PYTHONPATH environment variable. Then, you can run gridbots from any directory:

    python -m gridbots.run [sim_name]

I like to create a virtualenv for gridbots with virtualenvwrapper, and configure the PYTHONPATH 
using the postactivate/postdeactivate hooks.

### Implementation
The platform is implemented in Python, with a focus on simplicity and modularity. We want to define
specific components of functionality (initialization, planning, rendering) and maintain abstraction 
between them.

###### Bot
The Bot class represents a single microbot's components, graph location, and future goals. 

###### Simulation
The Simulation class constructs the graph and carries out the given simulation. The input is a 
simulation file and the output is a paths file specifying the trajectories of each Bot.

###### Renderer
The renderer is responsible for producing the output for the simulation. There are three types 
currently planned:

* The text renderer will output only a trajectory or control scheme, with no visuals. This is 
  useful when we want to control a physical system rather than simulate, and also for running very 
  large scale simulations in which rendering could be a bottleneck.
  
* The 2D renderer outputs a real-time top-view visualization of the system in action. The 
  PyGameDrawer achieves this using the PyGame python library for both timing and drawing. This is 
  most useful for simulating and understanding the platform with a simple visualization.
   
* The 3D renderer will produce a more compelling visual output of the system with meshes, textures, 
  and lighting using the Blender Game Engine This is most useful for producing 
  impressive and realistic looking videos.
