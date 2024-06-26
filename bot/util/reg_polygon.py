import math
from typing import List

from sc2.position import Point2

def n_sided_polygon_rad(n: int, radius = 1) -> List[Point2]:
    coords: List[Point2] = []
    angle = 2 * math.pi / n

    for idx in range(n):
        i = idx + 1
        a = angle * i
        x = radius
        y = 0
        x2 = y*math.sin(a) + x*math.cos(a)
        y2 = y*math.cos(a) - x*math.sin(a)
        coords.append(Point2((x2, y2)))
    return coords

def n_sided_polygon(n: int, distance = 22, offset_divisor=0) -> List[Point2]:
    points: List[Point2] = []

    angle = 2 * math.pi / n
    if offset_divisor == 0:
        starting_angle = 0
    else:
        starting_angle = angle / offset_divisor

    O = Point2((0, 0))
    A = Point2((math.cos(angle), math.sin(angle)))
    B = Point2((1, 0))

    C = A - B
    dOC = O.distance_to(C)
    scaling_factor = distance / dOC

    unit_coords: List[Point2] = []

    for idx in range(n):
        i = idx + 1
        a = angle * i + starting_angle
        x = 1
        y = 0
        x2 = y*math.sin(a) + x*math.cos(a)
        y2 = y*math.cos(a) - x*math.sin(a)
        unit_coords.append(Point2((x2, y2)))

    for point in unit_coords:
        points.append(Point2((point.x * scaling_factor, point.y * scaling_factor)))

    return points

def plot():
    import matplotlib.pyplot as plt
    import numpy as np
    points = n_sided_polygon(20)

    arr = []
    for point in points:
        arr.append([point.x, point.y])

    data = np.array(arr)
    x,y = data.T
    plt.scatter(x,y)
    plt.show()

def plot2():
    import matplotlib.pyplot as plt
    import numpy as np
    points = n_sided_polygon_rad(20, 20)

    arr = []
    for point in points:
        arr.append([point.x, point.y])

    data = np.array(arr)
    x,y = data.T
    plt.scatter(x,y)
    plt.show()