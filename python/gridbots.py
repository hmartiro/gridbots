"""

"""

from core.bot import Bot, Orientation
from core.simulation import Simulation

if __name__ == '__main__':

    a = Bot(x=3, y=4, orientation=Orientation.N)
    b = Bot(x=0, y=0, orientation=Orientation.W)

    moves = (
                (
                    (0,1),
                    (1,1),
                    (1,1),
                    (1,1),
                    (1,1),
                    (1,1),
                    (1,1),
                    (1,1),
                    (1,1)
                ), 
                (
                    (-1,0),
                    (1,-1),
                    (1,1),
                    (1,1),
                    (1,1),
                    (1,1),
                    (1,1),
                    (1,1),
                    (1,1)
                )
            )

    sim = Simulation(bots=[a, b], moves=moves)

    sim.run()
