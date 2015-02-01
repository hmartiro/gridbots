"""

"""

import numpy as np


def angle_between(u1, u2):
    """ Returns the angle in radians between vectors 'u1' and 'u2'.
        Assumes the vectors are normalized already.
    """
    angle = np.arccos(np.dot(u1, u2))
    if np.isnan(angle):
        return 0.0 if (u1 == u2).all() else np.pi
    return angle


def angle_from_x(v):
    """ Returns the angle of v from the positive x-axis, 0 to 2 pi.
    """
    assert len(v) == 2
    angle_from_y = -np.arctan2(v[0], v[1])
    if angle_from_y < 0:
        angle_from_y = np.pi + (np.pi + angle_from_y)

    return (angle_from_y + np.pi/2) % (2 * np.pi)


def rotation_between(v1, v2):
    """ Returns the correctly signed rotation in z needed to go
        from v1 to v2 in the XY plane.
    """
    theta = angle_between(v1, v2)
    theta1_x = angle_from_x(v1)
    theta2_x = angle_from_x(v2)
    if theta2_x >= theta1_x:
        sign = +1 if theta2_x - theta1_x < np.pi else -1
    else:
        sign = -1 if theta1_x - theta2_x < np.pi else +1
    return sign * theta
